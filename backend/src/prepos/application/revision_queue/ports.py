from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.revision_queue.entities import RevisionQueueItem


class RevisionQueueRepositoryPort(ABC):
    @abstractmethod
    async def upsert_queue_item(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        next_review_at: datetime,
        retention_score: Decimal | None,
        importance_score: Decimal,
        weakness_score: Decimal | None,
        priority_score: Decimal,
        status: str,
    ) -> RevisionQueueItem:
        raise NotImplementedError

    @abstractmethod
    async def delete_queue_item(
        self,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_due(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        exam_id: str | None = None,
        limit: int = 50,
    ) -> tuple[RevisionQueueItem, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_upcoming(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        exam_id: str | None = None,
        limit: int = 50,
    ) -> tuple[RevisionQueueItem, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_queue(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        exam_id: str | None = None,
        limit: int = 100,
    ) -> tuple[RevisionQueueItem, ...]:
        raise NotImplementedError

    @abstractmethod
    async def count_due(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        exam_id: str | None = None,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_high_risk(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        exam_id: str | None = None,
        weakness_threshold: Decimal | None = None,
    ) -> int:
        raise NotImplementedError
