from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.learning_graph.ports import LearningGraphRepositoryPort
from prepos.application.learning_graph.retention_materialization import materialize_node_retention
from prepos.application.revision_queue.ports import RevisionQueueRepositoryPort
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.revision_queue.events import RevisionQueueUpdated
from prepos.domain.revision_queue.priority_v1 import compute_priority_v1
from prepos.domain.revision_queue.value_objects import RevisionQueueStatus
from prepos.domain.scoring.weakness_v1 import WeaknessInputs, compute_weakness_v1
from prepos.events.outbox.publisher import OutboxPublisher


class RevisionQueueProjector:
    """Single-node revision queue projection; no full graph scans."""

    def __init__(
        self,
        *,
        graph_repo: LearningGraphRepositoryPort,
        queue_repo: RevisionQueueRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._graph_repo = graph_repo
        self._queue_repo = queue_repo
        self._outbox = outbox

    async def project_concept(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> str:
        now = current_time or datetime.now(UTC)
        node = await self._graph_repo.get_node(tenant_id, student_id, concept_id)

        if node is None or node.node_state == NodeStatus.UNRATED:
            deleted = await self._queue_repo.delete_queue_item(tenant_id, student_id, concept_id)
            action = "deleted" if deleted else "noop"
            if deleted:
                await self._emit_updated(
                    tenant_id=tenant_id,
                    student_id=student_id,
                    exam_id=exam_id,
                    concept_id=concept_id,
                    action=action,
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    occurred_at=now,
                )
            return action

        if node.node_state == NodeStatus.DEPRECATED:
            retention = materialize_node_retention(node, current_time=now)
            next_review_at = retention.next_review_at or now
            await self._queue_repo.upsert_queue_item(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                concept_id=concept_id,
                next_review_at=next_review_at,
                retention_score=retention.value,
                importance_score=node.importance_score,
                weakness_score=None,
                priority_score=Decimal("0.00"),
                status=RevisionQueueStatus.DEPRECATED,
            )
            await self._emit_updated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                concept_id=concept_id,
                action="deprecated",
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=now,
            )
            return "deprecated"

        retention = materialize_node_retention(node, current_time=now)
        if retention.next_review_at is None or node.retention_last_review_at is None:
            deleted = await self._queue_repo.delete_queue_item(tenant_id, student_id, concept_id)
            action = "deleted" if deleted else "noop"
            if deleted:
                await self._emit_updated(
                    tenant_id=tenant_id,
                    student_id=student_id,
                    exam_id=exam_id,
                    concept_id=concept_id,
                    action=action,
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    occurred_at=now,
                )
            return action

        error_rate = Decimal("0")
        if node.mcq_attempt_count > 0:
            error_rate = Decimal(node.mcq_attempt_count - node.mcq_correct_count) / Decimal(
                node.mcq_attempt_count
            )
        weakness = compute_weakness_v1(
            WeaknessInputs(
                mastery=node.mastery_score,
                retention=retention.value,
                confidence=node.confidence_score,
                error_rate=error_rate,
                unrated=False,
            )
        )
        weakness_score = weakness.value
        priority_score = compute_priority_v1(
            importance_score=node.importance_score,
            weakness_score=weakness_score,
            retention_score=retention.value,
        )
        status = (
            RevisionQueueStatus.DUE
            if retention.next_review_at <= now
            else RevisionQueueStatus.SCHEDULED
        )

        await self._queue_repo.upsert_queue_item(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            concept_id=concept_id,
            next_review_at=retention.next_review_at,
            retention_score=retention.value,
            importance_score=node.importance_score,
            weakness_score=weakness_score,
            priority_score=priority_score,
            status=status,
        )
        await self._emit_updated(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            concept_id=concept_id,
            action="upserted",
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=now,
        )
        return "upserted"

    async def _emit_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        action: str,
        correlation_id: str,
        causation_id: str | None,
        occurred_at: datetime,
    ) -> None:
        await self._outbox.enqueue_revision_queue_updated(
            RevisionQueueUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                concept_id=concept_id,
                action=action,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=occurred_at,
            )
        )
