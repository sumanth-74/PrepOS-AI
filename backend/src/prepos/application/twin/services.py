from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
from prepos.application.learning_graph.retention_materialization import (
    compute_due_for_revision,
    materialize_node_retention,
)
from prepos.application.twin.dto import TwinRecommendationResponse
from prepos.application.twin.ports import TwinRecommendationRepositoryPort
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.scoring.readiness_drivers_v1 import ReadinessDriversV1
from prepos.domain.scoring.readiness_v1_1 import ReadinessResultV1_1
from prepos.domain.scoring.weakness_v1 import WeaknessInputs, compute_weakness_v1
from prepos.domain.twin.entities import TwinRecommendation
from prepos.domain.twin.events import TwinRecommendationsUpdated
from prepos.domain.twin.recommendations_v1 import (
    TwinRecommendationInputs,
    compute_recommendation_for_concept,
    compute_twin_recommendations_v1,
)
from prepos.application.twin.personalization_service import PersonalizationService


class TwinRecommendationService:
    def __init__(
        self,
        *,
        learning_graph_read_service: LearningGraphReadService,
        recommendation_repo: TwinRecommendationRepositoryPort,
        outbox: OutboxPublisher,
        personalization_service: PersonalizationService | None = None,
    ) -> None:
        self._read_service = learning_graph_read_service
        self._recommendation_repo = recommendation_repo
        self._outbox = outbox
        self._personalization_service = personalization_service

    async def _readiness_context(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        current_time: datetime,
    ) -> tuple[LearningGraphReadinessSnapshot, ReadinessResultV1_1, ReadinessDriversV1 | None]:
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
        return readiness_snapshot, readiness_result, readiness_drivers

    async def _build_inputs(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        current_time: datetime | None = None,
    ) -> tuple[TwinRecommendationInputs, str]:
        now = current_time or datetime.now(UTC)
        rated_nodes = await self._read_service.list_rated_nodes(
            tenant_id=tenant_id,
            student_id=student_id,
        )
        exam_id = rated_nodes[0].exam_id if rated_nodes else ""

        weakness_by_concept: dict[str, Decimal] = {}
        for node in rated_nodes:
            error_rate = Decimal("0")
            if node.mcq_attempt_count > 0:
                error_rate = Decimal(node.mcq_attempt_count - node.mcq_correct_count) / Decimal(
                    node.mcq_attempt_count
                )
            weakness = compute_weakness_v1(
                WeaknessInputs(
                    mastery=node.mastery_score,
                    retention=materialize_node_retention(node, current_time=now).value,
                    confidence=node.confidence_score,
                    error_rate=error_rate,
                    unrated=node.node_state == NodeStatus.UNRATED,
                )
            )
            if weakness.value is not None:
                weakness_by_concept[node.concept_id] = weakness.value

        due_items = await self._read_service.list_due_revisions(
            tenant_id=tenant_id,
            student_id=student_id,
            limit=10_000,
            current_time=now,
        )
        due_concept_ids = frozenset(item.concept_id for item in due_items)
        readiness_snapshot, readiness_result, readiness_drivers = await self._readiness_context(
            tenant_id=tenant_id,
            student_id=student_id,
            current_time=now,
        )
        personalization = None
        if self._personalization_service is not None and exam_id:
            snapshot = await self._personalization_service.compute_personalization(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
            )
            personalization = snapshot.context

        return (
            TwinRecommendationInputs(
                nodes=rated_nodes,
                weakness_by_concept=weakness_by_concept,
                due_concept_ids=due_concept_ids,
                readiness_snapshot=readiness_snapshot,
                readiness_result=readiness_result,
                readiness_drivers=readiness_drivers,
                current_time=now,
                personalization=personalization,
            ),
            exam_id,
        )

    async def list_recommendations(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        limit: int = 20,
        current_time: datetime | None = None,
    ) -> list[TwinRecommendationResponse]:
        now = current_time or datetime.now(UTC)
        rated_nodes = await self._read_service.list_rated_nodes(tenant_id=tenant_id, student_id=student_id)
        exam_id = rated_nodes[0].exam_id if rated_nodes else ""
        if not exam_id:
            return []

        persisted = await self._recommendation_repo.list_recommendations(
            tenant_id,
            student_id,
            exam_id,
            limit=limit,
        )
        if not persisted:
            return []

        nodes_by_concept = {node.concept_id: node for node in rated_nodes}
        readiness_snapshot, readiness_result, readiness_drivers = await self._readiness_context(
            tenant_id=tenant_id,
            student_id=student_id,
            current_time=now,
        )
        responses: list[TwinRecommendationResponse] = []
        for row in persisted:
            node = nodes_by_concept.get(row.concept_id)
            if node is None:
                continue
            error_rate = Decimal("0")
            if node.mcq_attempt_count > 0:
                error_rate = Decimal(node.mcq_attempt_count - node.mcq_correct_count) / Decimal(
                    node.mcq_attempt_count
                )
            weakness = compute_weakness_v1(
                WeaknessInputs(
                    mastery=node.mastery_score,
                    retention=materialize_node_retention(node, current_time=now).value,
                    confidence=node.confidence_score,
                    error_rate=error_rate,
                    unrated=node.node_state == NodeStatus.UNRATED,
                )
            )
            if weakness.value is None:
                continue
            recommendation = compute_recommendation_for_concept(
                node,
                weakness_score=weakness.value,
                is_due=compute_due_for_revision(node, current_time=now),
                readiness_result=readiness_result,
                readiness_drivers=readiness_drivers,
                current_time=now,
            )
            if recommendation is None:
                continue
            responses.append(
                TwinRecommendationResponse(
                    concept_id=recommendation.concept_id,
                    recommendation_type=recommendation.recommendation_type,
                    recommendation_score=recommendation.recommendation_score,
                    importance_score=recommendation.importance_score,
                    weakness_score=recommendation.weakness_score,
                    retention_score=recommendation.retention_score,
                    readiness_gain=recommendation.readiness_gain,
                    explanation=recommendation.explanation,
                )
            )
        responses.sort(key=lambda item: (-item.readiness_gain, -item.recommendation_score, item.concept_id))
        return responses

    async def recompute_recommendation_for_concept(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> TwinRecommendation | None:
        now = current_time or datetime.now(UTC)
        node = await self._read_service.get_progress_node(
            tenant_id=tenant_id,
            student_id=student_id,
            concept_id=concept_id,
        )
        if node is None:
            await self._recommendation_repo.delete_recommendation(
                tenant_id,
                student_id,
                exam_id,
                concept_id,
            )
            await self._emit_recommendations_updated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=now,
            )
            return None

        error_rate = Decimal("0")
        if node.mcq_attempt_count > 0:
            error_rate = Decimal(node.mcq_attempt_count - node.mcq_correct_count) / Decimal(node.mcq_attempt_count)
        weakness = compute_weakness_v1(
            WeaknessInputs(
                mastery=node.mastery_score,
                retention=materialize_node_retention(node, current_time=now).value,
                confidence=node.confidence_score,
                error_rate=error_rate,
                unrated=node.node_state == NodeStatus.UNRATED,
            )
        )
        readiness_snapshot, readiness_result, readiness_drivers = await self._readiness_context(
            tenant_id=tenant_id,
            student_id=student_id,
            current_time=now,
        )
        recommendation = compute_recommendation_for_concept(
            node,
            weakness_score=weakness.value,
            is_due=compute_due_for_revision(node, current_time=now),
            readiness_result=readiness_result,
            readiness_drivers=readiness_drivers,
            current_time=now,
        )

        if recommendation is None:
            await self._recommendation_repo.delete_recommendation(
                tenant_id,
                student_id,
                exam_id,
                concept_id,
            )
        else:
            await self._recommendation_repo.upsert_recommendation(
                tenant_id,
                student_id,
                exam_id,
                recommendation,
            )

        await self._emit_recommendations_updated(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=now,
        )
        return recommendation

    async def recompute_and_persist(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> tuple[TwinRecommendation, ...]:
        """Full rebuild retained for backward compatibility."""
        inputs, resolved_exam_id = await self._build_inputs(
            tenant_id=tenant_id,
            student_id=student_id,
            current_time=current_time,
        )
        target_exam_id = exam_id or resolved_exam_id
        recommendations = compute_twin_recommendations_v1(inputs)
        await self._recommendation_repo.replace_recommendations(
            tenant_id,
            student_id,
            target_exam_id,
            recommendations,
        )
        await self._emit_recommendations_updated(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=target_exam_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=inputs.current_time,
        )
        return recommendations

    async def _emit_recommendations_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        occurred_at: datetime,
    ) -> None:
        summary = await self._recommendation_repo.get_recommendation_summary(
            tenant_id,
            student_id,
            exam_id,
        )
        await self._outbox.enqueue_twin_recommendations_updated(
            TwinRecommendationsUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                recommendation_count=summary.recommendation_count,
                concept_ids=tuple(item.concept_id for item in summary.top_recommendations),
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=occurred_at,
            )
        )
