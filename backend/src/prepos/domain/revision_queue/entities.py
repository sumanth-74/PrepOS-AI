from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RevisionQueueItem:
    id: UUID
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    concept_id: str
    next_review_at: datetime
    retention_score: Decimal | None
    importance_score: Decimal
    weakness_score: Decimal | None
    priority_score: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
