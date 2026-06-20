from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

import structlog

from prepos.application.goal.service import GoalService
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.memory.memory_service import CoachingMemoryService
from prepos.application.planning.adaptive_planning_engine import (
    DEFAULT_DAILY_MINUTES,
    PlanningCandidateInput,
    ScheduledPlanItem,
    build_candidate_from_signals,
    compute_planning_priority,
    generate_weekly_schedule,
)
from prepos.application.planning.planning_analytics import PlanningAnalyticsService
from prepos.application.planning.planning_explainer import explain_planning_decision
from prepos.application.planning.planning_models import (
    AdaptivePlanResponse,
    PlanCompletionResponse,
    PlanExplainResponse,
    PlanHistoryEntry,
    PlanHistoryResponse,
    PlanItemResponse,
    PlanRevisionResponse,
    PlanningAdminResponse,
)
from prepos.application.planning.ports import PlanningRepositoryPort
from prepos.application.pyq.ports import PyqRepositoryPort
from prepos.application.recommendations.recommendation_engine import format_concept_name
from prepos.application.recommendations.recommendation_service import LearningRecommendationService
from prepos.application.twin.twin_read_service import TwinReadService

logger = structlog.get_logger(__name__)


class AdaptivePlanningService:
    def __init__(
        self,
        *,
        repository: PlanningRepositoryPort,
        twin_read_service: TwinReadService,
        learning_graph_read_service: LearningGraphReadService,
        goal_service: GoalService,
        recommendation_service: LearningRecommendationService,
        memory_service: CoachingMemoryService,
        pyq_repository: PyqRepositoryPort,
        analytics_service: PlanningAnalyticsService | None = None,
    ) -> None:
        self._repository = repository
        self._twin_read_service = twin_read_service
        self._learning_graph_read_service = learning_graph_read_service
        self._goal_service = goal_service
        self._recommendation_service = recommendation_service
        self._memory_service = memory_service
        self._pyq_repository = pyq_repository
        self._analytics = analytics_service or PlanningAnalyticsService(repository=repository)

    async def generate_plan(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        exam_id: str,
        daily_minutes: int | None = None,
    ) -> AdaptivePlanResponse:
        resolved_exam_id = exam_id or "upsc_cse"
        now = datetime.now(UTC)
        start_date = now.date()
        valid_to = start_date + timedelta(days=13)
        budget = daily_minutes or await self._resolve_daily_minutes(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam_id,
        )

        candidates = await self._build_candidates(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            exam_id=resolved_exam_id,
        )
        today_items, week_items, next_week_draft = generate_weekly_schedule(
            candidates=candidates,
            start_date=start_date,
            daily_minutes=budget,
        )
        all_items = today_items + week_items + next_week_draft

        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam_id,
        )
        readiness = float(dashboard.readiness_score) if dashboard.readiness_score else None
        forecast = float(dashboard.projected_readiness) if dashboard.projected_readiness else None

        await self._repository.archive_active_plans(
            tenant_id=tenant_id,
            user_id=user_id,
            exam_id=resolved_exam_id,
            now=now,
        )
        plan_id = await self._repository.create_plan_version(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            exam_id=resolved_exam_id,
            generated_at=now,
            valid_from=start_date,
            valid_to=valid_to,
            readiness_snapshot=readiness,
            forecast_snapshot=forecast,
            status="active",
            now=now,
        )

        item_payloads = [_scheduled_to_payload(item) for item in all_items]
        item_ids = await self._repository.create_plan_items(plan_id=plan_id, items=item_payloads, now=now)

        await self._repository.record_event(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            plan_id=plan_id,
            item_id=None,
            concept_id=None,
            event_type="plan_generated",
            priority_score=None,
            estimated_gain=sum(item.estimated_readiness_gain for item in all_items),
            metadata_json={"item_count": len(all_items), "daily_minutes": budget},
            created_at=now,
        )
        logger.info(
            "study_plan_generated",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            concept_id=None,
            priority_score=None,
            estimated_gain=sum(item.estimated_readiness_gain for item in all_items),
        )

        response = self._build_plan_response(
            plan_id=plan_id,
            exam_id=resolved_exam_id,
            generated_at=now,
            valid_from=start_date,
            valid_to=valid_to,
            readiness_snapshot=readiness,
            forecast_snapshot=forecast,
            today_items=today_items,
            week_items=week_items,
            next_week_draft=next_week_draft,
            daily_minutes=budget,
            item_ids=item_ids,
        )
        return response

    async def get_current_plan(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
    ) -> AdaptivePlanResponse | None:
        resolved_exam_id = exam_id or "upsc_cse"
        row = await self._repository.get_current_plan(
            tenant_id=tenant_id,
            user_id=user_id,
            exam_id=resolved_exam_id,
        )
        if row is None:
            return None
        plan = row["plan"]
        items = row["items"]
        today = datetime.now(UTC).date()
        week_end = today + timedelta(days=6)
        next_week_end = today + timedelta(days=13)

        scheduled = [_model_to_scheduled(item) for item in items]
        today_items = [item for item in scheduled if item.scheduled_date == today]
        week_items = [item for item in scheduled if today <= item.scheduled_date <= week_end]
        next_week_draft = [item for item in scheduled if week_end < item.scheduled_date <= next_week_end]

        await self._repository.record_event(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=plan.student_id,
            plan_id=plan.id,
            item_id=None,
            concept_id=None,
            event_type="plan_viewed",
            priority_score=None,
            estimated_gain=None,
            metadata_json={},
            created_at=datetime.now(UTC),
        )

        return self._build_plan_response(
            plan_id=plan.id,
            exam_id=plan.exam_id,
            generated_at=plan.generated_at,
            valid_from=plan.valid_from,
            valid_to=plan.valid_to,
            readiness_snapshot=float(plan.readiness_snapshot) if plan.readiness_snapshot else None,
            forecast_snapshot=float(plan.forecast_snapshot) if plan.forecast_snapshot else None,
            today_items=today_items,
            week_items=week_items,
            next_week_draft=next_week_draft,
            daily_minutes=DEFAULT_DAILY_MINUTES,
            db_items=items,
        )

    async def get_plan_history(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
        limit: int = 20,
    ) -> PlanHistoryResponse:
        rows = await self._repository.list_plan_history(
            tenant_id=tenant_id,
            user_id=user_id,
            exam_id=exam_id or "upsc_cse",
            limit=limit,
        )
        plans = [
            PlanHistoryEntry(
                plan_id=row["plan"].id,
                generated_at=row["plan"].generated_at,
                valid_from=row["plan"].valid_from,
                valid_to=row["plan"].valid_to,
                status=row["plan"].status,
                item_count=int(row["item_count"]),
                completed_count=int(row["completed_count"]),
            )
            for row in rows
        ]
        return PlanHistoryResponse(plans=plans, total=len(plans))

    async def complete_item(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        item_id: UUID,
    ) -> PlanCompletionResponse:
        now = datetime.now(UTC)
        row = await self._repository.mark_item_completed(
            tenant_id=tenant_id,
            item_id=item_id,
            now=now,
        )
        if row is None:
            raise ValueError("Plan item not found.")
        item = row["item"]
        plan = row["plan"]
        await self._repository.record_event(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=plan.student_id,
            plan_id=plan.id,
            item_id=item.id,
            concept_id=item.concept_id,
            event_type="plan_item_completed",
            priority_score=float(item.priority_score),
            estimated_gain=float(item.estimated_readiness_gain),
            metadata_json={"activity_type": item.activity_type},
            created_at=now,
        )
        logger.info(
            "study_plan_completed",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            concept_id=item.concept_id,
            priority_score=float(item.priority_score),
            estimated_gain=float(item.estimated_readiness_gain),
        )
        return PlanCompletionResponse(
            item_id=item.id,
            concept_id=item.concept_id,
            completion_status=item.completion_status,
            estimated_readiness_gain=float(item.estimated_readiness_gain),
        )

    async def explain_concept(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
    ) -> PlanExplainResponse:
        candidates = await self._build_candidates(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            exam_id=exam_id or "upsc_cse",
        )
        candidate = next((item for item in candidates if item.concept_id == concept_id), None)
        if candidate is None:
            candidate = build_candidate_from_signals(
                concept_id=concept_id,
                weakness_score=0.0,
                impact_score=0.0,
                pyq_frequency=0.0,
                pyq_count=0,
                readiness_gain=0.0,
                gap_to_goal=0.0,
                importance_score=0.0,
                memory_effectiveness=0.0,
            )
        breakdown = compute_planning_priority(candidate)
        source_reason = ", ".join(breakdown.reason_codes) or "balanced planning priority"
        explanations = explain_planning_decision(breakdown=breakdown, source_reason=source_reason)
        activity_type = "HIGH_IMPORTANCE_STUDY"
        from prepos.application.planning.adaptive_planning_engine import (
            estimate_plan_gain,
            estimate_plan_minutes,
            plan_confidence,
        )

        return PlanExplainResponse(
            concept_id=concept_id,
            concept_name=format_concept_name(concept_id),
            priority_score=breakdown.priority_score,
            estimated_readiness_gain=estimate_plan_gain(
                priority_score=breakdown.priority_score,
                weakness_score=candidate.weakness_score,
            ),
            estimated_minutes=estimate_plan_minutes(
                priority_score=breakdown.priority_score,
                activity_type=activity_type,
            ),
            confidence=plan_confidence(
                priority_score=breakdown.priority_score,
                reason_count=len(breakdown.reason_codes),
            ),
            source_reason=source_reason,
            score_breakdown=breakdown,
            explanations=explanations,
        )

    async def get_admin_dashboard(self, *, tenant_id: UUID) -> PlanningAdminResponse:
        metrics = await self._analytics.get_admin_dashboard(tenant_id=tenant_id)
        return PlanningAdminResponse(
            total_plans=int(metrics["total_plans"]),
            active_plans=int(metrics["active_plans"]),
            plans_generated_last_30_days=int(metrics["plans_generated_last_30_days"]),
            average_completion_rate=float(metrics["average_completion_rate"]),
            average_adherence=float(metrics["average_adherence"]),
            top_scheduled_concepts=list(metrics["top_scheduled_concepts"]),
            event_counts=list(metrics["event_counts"]),
        )

    async def export_csv(self, *, tenant_id: UUID) -> str:
        return await self._analytics.export_csv(tenant_id=tenant_id)

    async def list_revisions(self, *, tenant_id: UUID, user_id: UUID, exam_id: str) -> list[PlanRevisionResponse]:
        row = await self._repository.get_current_plan(
            tenant_id=tenant_id,
            user_id=user_id,
            exam_id=exam_id or "upsc_cse",
        )
        if row is None:
            return []
        revisions = await self._repository.list_revisions(plan_id=row["plan"].id, limit=50)
        return [
            PlanRevisionResponse(
                id=entry["revision"].id,
                concept_id=entry["revision"].concept_id,
                revision_reason=entry["revision"].revision_reason,
                old_priority=float(entry["revision"].old_priority) if entry["revision"].old_priority else None,
                new_priority=float(entry["revision"].new_priority) if entry["revision"].new_priority else None,
                created_at=entry["revision"].created_at,
            )
            for entry in revisions
        ]

    async def _build_candidates(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> list[PlanningCandidateInput]:
        recommendations = await self._recommendation_service.get_student_recommendations(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            user_id=user_id,
            limit=20,
        )
        weaknesses = await self._learning_graph_read_service.get_weaknesses(
            tenant_id=tenant_id,
            student_id=student_id,
            limit=20,
        )
        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        goal = await self._goal_service.get_goal(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        pyq_stats = await self._pyq_repository.list_statistics(exam_id=exam_id, limit=100)
        memory_context = await self._memory_service.load_student_context(
            tenant_id=tenant_id,
            user_id=user_id,
        )
        memory_by_concept: dict[str, float] = {}
        for outcome in memory_context.outcome_summaries:
            concept_id = str(outcome.memory_value.get("concept_id") or "")
            if concept_id:
                memory_by_concept[concept_id] = float(outcome.memory_value.get("effectiveness_score", 0))

        weakness_by_concept = {item.concept_id: item for item in weaknesses.weaknesses}
        pyq_by_concept = {item.concept_id: item for item in pyq_stats}
        rec_by_concept = {item.concept_id: item for item in recommendations.recommendations}

        concept_ids = set(weakness_by_concept) | set(rec_by_concept) | set(pyq_by_concept)
        candidates: list[PlanningCandidateInput] = []
        gap_to_goal = float(goal.goal_probability) if goal and goal.goal_probability else None
        for concept_id in sorted(concept_ids):
            weakness = weakness_by_concept.get(concept_id)
            rec = rec_by_concept.get(concept_id)
            pyq = pyq_by_concept.get(concept_id)
            candidates.append(
                build_candidate_from_signals(
                    concept_id=concept_id,
                    weakness_score=float(weakness.weakness_score) if weakness else None,
                    impact_score=rec.impact_score if rec else None,
                    pyq_frequency=float(pyq.frequency_score) if pyq else None,
                    pyq_count=pyq.pyq_count if pyq else 0,
                    readiness_gain=rec.estimated_readiness_gain if rec else None,
                    gap_to_goal=gap_to_goal,
                    importance_score=float(weakness.importance_score) if weakness else None,
                    memory_effectiveness=memory_by_concept.get(concept_id),
                )
            )
        return candidates

    async def _resolve_daily_minutes(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> int:
        goal = await self._goal_service.get_goal(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        if goal and goal.daily_capacity_minutes:
            return int(goal.daily_capacity_minutes)
        return DEFAULT_DAILY_MINUTES

    def _build_plan_response(
        self,
        *,
        plan_id: UUID,
        exam_id: str,
        generated_at: datetime,
        valid_from: date,
        valid_to: date,
        readiness_snapshot: float | None,
        forecast_snapshot: float | None,
        today_items: list[ScheduledPlanItem],
        week_items: list[ScheduledPlanItem],
        next_week_draft: list[ScheduledPlanItem],
        daily_minutes: int,
        item_ids: list[UUID] | None = None,
        db_items: list[object] | None = None,
    ) -> AdaptivePlanResponse:
        all_scheduled = today_items + week_items + next_week_draft

        if db_items is not None:
            model_by_key = {
                (model.concept_id, model.scheduled_date.isoformat(), model.activity_type): model  # type: ignore[attr-defined]
                for model in db_items
            }

            def map_items(bucket: list[ScheduledPlanItem]) -> list[PlanItemResponse]:
                responses: list[PlanItemResponse] = []
                for item in bucket:
                    model = model_by_key[(item.concept_id, item.scheduled_date.isoformat(), item.activity_type)]
                    responses.append(
                        _scheduled_to_response(
                            item,
                            item_id=model.id,  # type: ignore[attr-defined]
                            completion_status=model.completion_status,  # type: ignore[attr-defined]
                        )
                    )
                return responses
        elif item_ids is not None:
            id_iter = iter(item_ids)

            def map_items(bucket: list[ScheduledPlanItem]) -> list[PlanItemResponse]:
                return [_scheduled_to_response(item, item_id=next(id_iter)) for item in bucket]
        else:
            def map_items(bucket: list[ScheduledPlanItem]) -> list[PlanItemResponse]:
                from uuid import uuid4

                return [_scheduled_to_response(item, item_id=uuid4()) for item in bucket]

        return AdaptivePlanResponse(
            plan_id=plan_id,
            exam_id=exam_id,
            generated_at=generated_at,
            valid_from=valid_from,
            valid_to=valid_to,
            readiness_snapshot=readiness_snapshot,
            forecast_snapshot=forecast_snapshot,
            status="active",
            today_items=map_items(today_items),
            week_items=map_items(week_items),
            next_week_draft=map_items(next_week_draft),
            total_estimated_gain=round(sum(item.estimated_readiness_gain for item in all_scheduled), 2),
            daily_minutes_budget=daily_minutes,
        )


def _scheduled_to_payload(item: ScheduledPlanItem) -> dict[str, object]:
    return {
        "concept_id": item.concept_id,
        "activity_type": item.activity_type,
        "priority_score": item.priority_score,
        "estimated_minutes": item.estimated_minutes,
        "estimated_readiness_gain": item.estimated_readiness_gain,
        "confidence": item.confidence,
        "scheduled_date": item.scheduled_date,
        "source_reason": item.source_reason,
    }


def _scheduled_to_response(
    item: ScheduledPlanItem,
    *,
    item_id: UUID,
    completion_status: str = "pending",
) -> PlanItemResponse:
    return PlanItemResponse(
        id=item_id,
        concept_id=item.concept_id,
        concept_name=item.concept_name,
        activity_type=item.activity_type,
        priority_score=item.priority_score,
        estimated_minutes=item.estimated_minutes,
        estimated_readiness_gain=item.estimated_readiness_gain,
        confidence=item.confidence,
        scheduled_date=item.scheduled_date,
        source_reason=item.source_reason,
        completion_status=completion_status,
    )


def _model_to_scheduled(item: object) -> ScheduledPlanItem:
    model = item
    return ScheduledPlanItem(
        concept_id=model.concept_id,  # type: ignore[attr-defined]
        concept_name=format_concept_name(model.concept_id),  # type: ignore[attr-defined]
        activity_type=model.activity_type,  # type: ignore[attr-defined]
        priority_score=float(model.priority_score),  # type: ignore[attr-defined]
        estimated_minutes=int(model.estimated_minutes),  # type: ignore[attr-defined]
        estimated_readiness_gain=float(model.estimated_readiness_gain),  # type: ignore[attr-defined]
        confidence=model.confidence,  # type: ignore[attr-defined]
        scheduled_date=model.scheduled_date,  # type: ignore[attr-defined]
        source_reason=model.source_reason,  # type: ignore[attr-defined]
        score_breakdown=compute_planning_priority(
            build_candidate_from_signals(
                concept_id=model.concept_id,  # type: ignore[attr-defined]
                weakness_score=float(model.priority_score),  # type: ignore[attr-defined]
                impact_score=float(model.priority_score) / 10.0,  # type: ignore[attr-defined]
                pyq_frequency=0.0,
                pyq_count=0,
                readiness_gain=float(model.estimated_readiness_gain),  # type: ignore[attr-defined]
                gap_to_goal=0.0,
                importance_score=0.0,
                memory_effectiveness=0.0,
            )
        ),
    )
