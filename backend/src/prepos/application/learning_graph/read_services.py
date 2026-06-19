from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.learning_graph.dto import (
    ConceptProgressNodeResponse,
    DueRevisionItemResponse,
    LearningGraphOverviewResponse,
    LearningGraphReadinessResponse,
    LearningGraphReadinessSnapshotResponse,
    LearningGraphSummaryResponse,
    LearningGraphWeaknessesResponse,
    WeaknessItemResponse,
)
from prepos.application.learning_graph.ports import LearningGraphReadRepositoryPort, LearningGraphRepositoryPort
from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
from prepos.application.learning_graph.retention_materialization import (
    compute_due_for_revision,
    compute_graph_score_aggregates,
    due_revision_sort_key,
    materialize_node_retention,
)
from prepos.domain.learning_graph.entities import (
    ConceptProgressNode,
    DueRevisionItem,
    LearningGraphReadinessSnapshot,
    StudentGraphSummary,
)
from prepos.domain.learning_graph.exceptions import NodeNotFoundError
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.scoring.weakness_v1 import WeaknessInputs, compute_weakness_v1
from prepos.infrastructure.cache.learning_graph_cache import LearningGraphCachePort


def _node_to_dto(node: object, *, current_time: datetime | None = None) -> ConceptProgressNodeResponse:
    from prepos.domain.learning_graph.entities import ConceptProgressNode

    assert isinstance(node, ConceptProgressNode)
    now = current_time or datetime.now(UTC)
    retention = materialize_node_retention(node, current_time=now)
    return ConceptProgressNodeResponse(
        concept_id=node.concept_id,
        exam_id=node.exam_id,
        subject_id=node.subject_id,
        topic_id=node.topic_id,
        mastery_score=node.mastery_score,
        mastery_nonmcq_score=node.mastery_nonmcq_score,
        retention_score=retention.value,
        confidence_score=node.confidence_score,
        importance_score=node.importance_score,
        overconfidence_flag=node.overconfidence_flag,
        mcq_attempt_count=node.mcq_attempt_count,
        mcq_correct_count=node.mcq_correct_count,
        nonmcq_attempt_count=node.nonmcq_attempt_count,
        revision_count=node.revision_count,
        study_minutes=node.study_minutes,
        node_state=node.node_state,
        row_version=node.row_version,
        last_activity_at=node.last_activity_at,
        retention_stability_s=node.retention_stability_s,
        retention_last_event_at=node.retention_last_event_at,
        retention_last_review_at=node.retention_last_review_at,
        retention_last_grade=node.retention_last_grade,
        next_review_at=retention.next_review_at,
    )


class LearningGraphReadService:
    def __init__(
        self,
        *,
        read_repo: LearningGraphReadRepositoryPort,
        write_repo: LearningGraphRepositoryPort,
        cache: LearningGraphCachePort,
    ) -> None:
        self._read_repo = read_repo
        self._write_repo = write_repo
        self._cache = cache

    async def _materialized_retention_average(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        current_time: datetime | None = None,
    ) -> Decimal | None:
        rated_nodes = await self._read_repo.list_rated_nodes(tenant_id, student_id)
        return compute_graph_score_aggregates(rated_nodes, current_time=current_time).average_retention

    async def get_overview(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        limit: int = 50,
    ) -> LearningGraphOverviewResponse:
        provision = await self._read_repo.get_provision(tenant_id, student_id)
        nodes = await self._read_repo.list_nodes(tenant_id, student_id, limit=limit)
        exam_id = nodes[0].exam_id if nodes else ""
        if provision is None:
            expected, provisioned, status = 0, 0, "missing"
        else:
            expected, provisioned, status = provision
        return LearningGraphOverviewResponse(
            student_id=student_id,
            exam_id=exam_id,
            total_nodes=await self._write_repo.count_nodes(tenant_id, student_id),
            provisioned_nodes=provisioned,
            expected_nodes=expected,
            provision_status=status,
            nodes=[_node_to_dto(node) for node in nodes],
        )

    async def get_summary(self, *, tenant_id: UUID, student_id: UUID) -> LearningGraphSummaryResponse:
        cached = await self._cache.get_summary(tenant_id, student_id)
        if cached is not None:
            average_retention = await self._materialized_retention_average(
                tenant_id=tenant_id,
                student_id=student_id,
            )
            return LearningGraphSummaryResponse(
                student_id=student_id,
                exam_id=cached.exam_id,
                total_nodes=cached.total_nodes,
                active_nodes=cached.active_nodes,
                average_mastery=cached.average_mastery,
                average_retention=average_retention,
                average_confidence=cached.average_confidence,
            )

        summary = await self._read_repo.get_summary(tenant_id, student_id)
        if summary is None:
            return LearningGraphSummaryResponse(
                student_id=student_id,
                exam_id="",
                total_nodes=0,
                active_nodes=0,
                average_mastery=None,
                average_retention=None,
                average_confidence=None,
            )

        average_retention = await self._materialized_retention_average(
            tenant_id=tenant_id,
            student_id=student_id,
        )

        materialized_summary = StudentGraphSummary(
            tenant_id=summary.tenant_id,
            student_id=summary.student_id,
            exam_id=summary.exam_id,
            total_nodes=summary.total_nodes,
            active_nodes=summary.active_nodes,
            average_mastery=summary.average_mastery,
            average_retention=average_retention,
            average_confidence=summary.average_confidence,
            weakest_concept_ids=summary.weakest_concept_ids,
        )
        await self._cache.set_summary(materialized_summary)
        return LearningGraphSummaryResponse(
            student_id=student_id,
            exam_id=summary.exam_id,
            total_nodes=summary.total_nodes,
            active_nodes=summary.active_nodes,
            average_mastery=summary.average_mastery,
            average_retention=average_retention,
            average_confidence=summary.average_confidence,
        )

    async def get_readiness_snapshot(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        current_time: datetime | None = None,
    ) -> LearningGraphReadinessSnapshotResponse:
        rated_nodes = await self._read_repo.list_rated_nodes(tenant_id, student_id)
        aggregates = compute_graph_score_aggregates(rated_nodes, current_time=current_time)
        total_node_count = await self._write_repo.count_nodes(tenant_id, student_id)
        snapshot = LearningGraphReadinessSnapshot(
            average_mastery=aggregates.average_mastery,
            average_retention=aggregates.average_retention,
            average_confidence=aggregates.average_confidence,
            rated_node_count=aggregates.rated_node_count,
            total_node_count=total_node_count,
        )
        return LearningGraphReadinessSnapshotResponse(
            student_id=student_id,
            average_mastery=snapshot.average_mastery,
            average_retention=snapshot.average_retention,
            average_confidence=snapshot.average_confidence,
            rated_node_count=snapshot.rated_node_count,
            total_node_count=snapshot.total_node_count,
        )

    async def get_readiness(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        current_time: datetime | None = None,
    ) -> LearningGraphReadinessResponse:
        snapshot_response = await self.get_readiness_snapshot(
            tenant_id=tenant_id,
            student_id=student_id,
            current_time=current_time,
        )
        snapshot = LearningGraphReadinessSnapshot(
            average_mastery=snapshot_response.average_mastery,
            average_retention=snapshot_response.average_retention,
            average_confidence=snapshot_response.average_confidence,
            rated_node_count=snapshot_response.rated_node_count,
            total_node_count=snapshot_response.total_node_count,
        )
        result, _ = compute_readiness_from_snapshot(snapshot)
        return LearningGraphReadinessResponse(
            version=result.version,
            overall_score=result.overall_score,
            knowledge_subscore=result.knowledge_subscore,
            retention_subscore=result.retention_subscore,
            confidence_subscore=result.confidence_subscore,
            coverage_subscore=result.coverage_subscore,
            rated_node_count=result.rated_node_count,
            total_node_count=result.total_node_count,
            unrated=result.unrated,
            readiness_score=result.overall_score,
        )

    async def list_due_revisions(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        limit: int = 50,
        current_time: datetime | None = None,
    ) -> list[DueRevisionItemResponse]:
        now = current_time or datetime.now(UTC)
        rated_nodes = await self._read_repo.list_rated_nodes(tenant_id, student_id)
        due_nodes = [
            node
            for node in rated_nodes
            if compute_due_for_revision(node, current_time=now)
        ]
        due_nodes.sort(key=lambda node: due_revision_sort_key(node, current_time=now))

        items: list[DueRevisionItemResponse] = []
        for node in due_nodes[:limit]:
            retention = materialize_node_retention(node, current_time=now)
            assert retention.next_review_at is not None
            assert retention.value is not None
            item = DueRevisionItem(
                student_id=student_id,
                concept_id=node.concept_id,
                next_review_at=retention.next_review_at,
                retention_score=retention.value,
                importance_score=node.importance_score,
            )
            items.append(
                DueRevisionItemResponse(
                    concept_id=item.concept_id,
                    next_review_at=item.next_review_at,
                    retention_score=item.retention_score,
                    importance_score=item.importance_score,
                )
            )
        return items

    async def get_node(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> ConceptProgressNodeResponse:
        cached = await self._cache.get_node(tenant_id, student_id, concept_id)
        if cached is not None:
            return _node_to_dto(cached)

        node = await self._write_repo.get_node(tenant_id, student_id, concept_id)
        if node is None:
            raise NodeNotFoundError(
                "Concept progress node not found.",
                details={"concept_id": concept_id, "student_id": str(student_id)},
            )
        await self._cache.set_node(node)
        return _node_to_dto(node)

    async def get_progress_node(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> ConceptProgressNode | None:
        cached = await self._cache.get_node(tenant_id, student_id, concept_id)
        if cached is not None:
            return cached

        node = await self._write_repo.get_node(tenant_id, student_id, concept_id)
        if node is not None:
            await self._cache.set_node(node)
        return node

    async def get_weaknesses(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        limit: int = 10,
    ) -> LearningGraphWeaknessesResponse:
        nodes = await self._read_repo.list_weakest_nodes(tenant_id, student_id, limit=limit)
        weaknesses: list[WeaknessItemResponse] = []
        for node in nodes:
            error_rate = Decimal("0")
            if node.mcq_attempt_count > 0:
                error_rate = Decimal(node.mcq_attempt_count - node.mcq_correct_count) / Decimal(node.mcq_attempt_count)
            materialized_retention = materialize_node_retention(node).value
            weakness = compute_weakness_v1(
                WeaknessInputs(
                    mastery=node.mastery_score,
                    retention=materialized_retention,
                    confidence=node.confidence_score,
                    error_rate=error_rate,
                    unrated=node.node_state == NodeStatus.UNRATED,
                )
            )
            if weakness.value is None:
                continue
            weaknesses.append(
                WeaknessItemResponse(
                    concept_id=node.concept_id,
                    mastery_score=node.mastery_score,
                    retention_score=materialized_retention,
                    importance_score=node.importance_score,
                    weakness_score=weakness.value,
                )
            )
        return LearningGraphWeaknessesResponse(student_id=student_id, weaknesses=weaknesses)

    async def list_rated_nodes(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
    ) -> tuple[ConceptProgressNode, ...]:
        return await self._read_repo.list_rated_nodes(tenant_id, student_id)
