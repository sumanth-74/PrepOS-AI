from __future__ import annotations

from uuid import UUID

from prepos.application.revision_queue.dto import RevisionQueueItemResponse
from prepos.application.revision_queue.ports import RevisionQueueRepositoryPort


class RevisionQueueReadService:
    def __init__(self, *, queue_repo: RevisionQueueRepositoryPort) -> None:
        self._queue_repo = queue_repo

    async def list_queue(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None = None,
        limit: int = 100,
    ) -> list[RevisionQueueItemResponse]:
        items = await self._queue_repo.list_queue(
            tenant_id,
            student_id,
            exam_id=exam_id,
            limit=limit,
        )
        return [
            RevisionQueueItemResponse(
                concept_id=item.concept_id,
                status=item.status,
                priority_score=item.priority_score,
                next_review_at=item.next_review_at,
                retention_score=item.retention_score,
                weakness_score=item.weakness_score,
                importance_score=item.importance_score,
            )
            for item in items
        ]
