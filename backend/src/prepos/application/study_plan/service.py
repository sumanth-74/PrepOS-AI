from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.goal.forecast_service import ForecastService
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
from prepos.application.learning_graph.retention_materialization import (
    materialize_node_retention,
)
from prepos.application.revision_queue.ports import RevisionQueueRepositoryPort
from prepos.application.study_plan.dto import DailyPlanItemResponse, StudyPlanResponse, WeeklyPlanItemResponse
from prepos.application.study_plan.execution_tracker import StudyPlanExecutionTracker
from prepos.application.study_plan.ports import StudyPlanExecutionRepositoryPort, StudyPlanRepositoryPort
from prepos.application.twin.ports import TwinRecommendationRepositoryPort
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.revision_queue.value_objects import RevisionQueueStatus
from prepos.domain.scoring.weakness_v1 import WeaknessInputs, compute_weakness_v1
from prepos.domain.study_plan.entities import StudyPlan
from prepos.domain.study_plan.events import StudyPlanUpdated
from prepos.application.twin.personalization_service import PersonalizationService
from prepos.domain.study_plan.plan_generator_v1 import PlanGeneratorInputs, generate_study_plan_v1
from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle
from prepos.domain.twin.entities import TwinRecommendation
from prepos.domain.twin.recommendations_v1 import TwinRecommendationInputs, compute_twin_recommendations_v1
from prepos.events.outbox.publisher import OutboxPublisher


class StudyPlanService:
    def __init__(
        self,
        *,
        read_service: LearningGraphReadService,
        recommendation_repo: TwinRecommendationRepositoryPort,
        queue_repo: RevisionQueueRepositoryPort,
        study_plan_repo: StudyPlanRepositoryPort,
        execution_repo: StudyPlanExecutionRepositoryPort,
        execution_tracker: StudyPlanExecutionTracker,
        forecast_service: ForecastService,
        outbox: OutboxPublisher,
        personalization_service: PersonalizationService | None = None,
    ) -> None:
        self._read_service = read_service
        self._recommendation_repo = recommendation_repo
        self._queue_repo = queue_repo
        self._study_plan_repo = study_plan_repo
        self._execution_repo = execution_repo
        self._execution_tracker = execution_tracker
        self._forecast_service = forecast_service
        self._outbox = outbox
        self._personalization_service = personalization_service

    async def rebuild_study_plan(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
        daily_capacity_minutes: int | None = None,
    ) -> StudyPlanResponse:
        now = current_time or datetime.now(UTC)
        recommendations = await self._load_recommendations(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=now,
        )
        due_queue = await self._queue_repo.list_due(
            tenant_id,
            student_id,
            exam_id=exam_id,
            limit=100,
        )
        snapshot_response = await self._read_service.get_readiness_snapshot(
            tenant_id=tenant_id,
            student_id=student_id,
            current_time=now,
        )
        readiness_snapshot = LearningGraphReadinessSnapshot(
            average_mastery=snapshot_response.average_mastery,
            average_retention=snapshot_response.average_retention,
            average_confidence=snapshot_response.average_confidence,
            rated_node_count=snapshot_response.rated_node_count,
            total_node_count=snapshot_response.total_node_count,
        )
        behavior_metrics = await self._execution_repo.get_behavior_metrics(
            tenant_id,
            student_id,
            exam_id,
        )
        capacity = daily_capacity_minutes
        if capacity is None:
            capacity = await self._forecast_service.resolve_daily_capacity(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                current_time=now,
            )

        learning_style: LearningStyle | None = None
        if self._personalization_service is not None:
            personalization = await self._personalization_service.compute_personalization(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
            )
            learning_style = personalization.summary.learning_style

        plan = generate_study_plan_v1(
            PlanGeneratorInputs(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                recommendations=recommendations,
                revision_queue=tuple(
                    item for item in due_queue if item.status == RevisionQueueStatus.DUE
                ),
                readiness_snapshot=readiness_snapshot,
                behavior_metrics=behavior_metrics,
                learning_style=learning_style,
                generated_at=now,
                default_daily_minutes=capacity,
            )
        )
        persisted = await self._study_plan_repo.upsert_study_plan(plan)
        await self._emit_study_plan_updated(
            plan=persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=now,
        )
        return self._to_response(persisted)

    async def get_study_plan(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None = None,
    ) -> StudyPlanResponse:
        if exam_id is not None:
            plan = await self._study_plan_repo.get_study_plan(tenant_id, student_id, exam_id)
        else:
            plan = await self._study_plan_repo.get_study_plan_for_student(tenant_id, student_id)
        if plan is None:
            return StudyPlanResponse()
        return self._to_response(plan)

    async def record_item_completed(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        activity_type: ActivityType,
        planned_minutes: int,
        actual_minutes: int,
        correlation_id: str,
        causation_id: str | None,
        completed_at: datetime | None = None,
    ) -> None:
        await self._execution_tracker.request_item_completed(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            concept_id=concept_id,
            activity_type=activity_type,
            planned_minutes=planned_minutes,
            actual_minutes=actual_minutes,
            completed_at=completed_at or datetime.now(UTC),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    async def record_item_skipped(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        activity_type: ActivityType,
        planned_minutes: int,
        actual_minutes: int,
        correlation_id: str,
        causation_id: str | None,
        completed_at: datetime | None = None,
    ) -> None:
        await self._execution_tracker.request_item_skipped(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            concept_id=concept_id,
            activity_type=activity_type,
            planned_minutes=planned_minutes,
            actual_minutes=actual_minutes,
            completed_at=completed_at or datetime.now(UTC),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    async def _load_recommendations(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        current_time: datetime,
    ) -> tuple[TwinRecommendation, ...]:
        rated_nodes = await self._read_service.list_rated_nodes(tenant_id=tenant_id, student_id=student_id)
        if not rated_nodes:
            return ()

        weakness_by_concept: dict[str, Decimal] = {}
        for node in rated_nodes:
            if node.exam_id != exam_id:
                continue
            error_rate = Decimal("0")
            if node.mcq_attempt_count > 0:
                error_rate = Decimal(node.mcq_attempt_count - node.mcq_correct_count) / Decimal(
                    node.mcq_attempt_count
                )
            weakness = compute_weakness_v1(
                WeaknessInputs(
                    mastery=node.mastery_score,
                    retention=materialize_node_retention(node, current_time=current_time).value,
                    confidence=node.confidence_score,
                    error_rate=error_rate,
                    unrated=node.node_state == NodeStatus.UNRATED,
                )
            )
            if weakness.value is not None:
                weakness_by_concept[node.concept_id] = weakness.value

        exam_nodes = tuple(node for node in rated_nodes if node.exam_id == exam_id)
        if not exam_nodes:
            return ()

        due_items = await self._read_service.list_due_revisions(
            tenant_id=tenant_id,
            student_id=student_id,
            limit=10_000,
            current_time=current_time,
        )
        due_concept_ids = frozenset(item.concept_id for item in due_items)

        snapshot_response = await self._read_service.get_readiness_snapshot(
            tenant_id=tenant_id,
            student_id=student_id,
            current_time=current_time,
        )
        readiness_snapshot = LearningGraphReadinessSnapshot(
            average_mastery=snapshot_response.average_mastery,
            average_retention=snapshot_response.average_retention,
            average_confidence=snapshot_response.average_confidence,
            rated_node_count=snapshot_response.rated_node_count,
            total_node_count=snapshot_response.total_node_count,
        )
        readiness_result, readiness_drivers = compute_readiness_from_snapshot(readiness_snapshot)

        return compute_twin_recommendations_v1(
            TwinRecommendationInputs(
                nodes=exam_nodes,
                weakness_by_concept=weakness_by_concept,
                due_concept_ids=due_concept_ids,
                readiness_snapshot=readiness_snapshot,
                readiness_result=readiness_result,
                readiness_drivers=readiness_drivers,
                current_time=current_time,
            )
        )

    async def _emit_study_plan_updated(
        self,
        *,
        plan: StudyPlan,
        correlation_id: str,
        causation_id: str | None,
        occurred_at: datetime,
    ) -> None:
        await self._outbox.enqueue_study_plan_updated(
            StudyPlanUpdated(
                tenant_id=plan.tenant_id,
                student_id=plan.student_id,
                exam_id=plan.exam_id,
                daily_item_count=len(plan.daily_plan),
                weekly_item_count=len(plan.weekly_plan),
                total_estimated_gain=plan.total_estimated_gain,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=occurred_at,
            )
        )

    @staticmethod
    def _to_response(plan: StudyPlan) -> StudyPlanResponse:
        return StudyPlanResponse(
            generated_at=plan.generated_at,
            total_estimated_gain=plan.total_estimated_gain,
            daily_plan=[
                DailyPlanItemResponse(
                    concept_id=item.concept_id,
                    activity_type=item.activity_type.value,
                    estimated_minutes=item.estimated_minutes,
                    priority_score=item.priority_score,
                    adaptive_priority=item.adaptive_priority,
                    readiness_gain=item.readiness_gain,
                    adjustment_explanation=item.adjustment_explanation,
                )
                for item in plan.daily_plan
            ],
            weekly_plan=[
                WeeklyPlanItemResponse(
                    concept_id=item.concept_id,
                    target_sessions=item.target_sessions,
                    estimated_minutes=item.estimated_minutes,
                    readiness_gain=item.readiness_gain,
                )
                for item in plan.weekly_plan
            ],
        )
