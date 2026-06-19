from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PreparationGoal:
    id: UUID
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    target_readiness_score: Decimal
    target_date: date
    daily_capacity_minutes: int
    created_at: datetime
    updated_at: datetime
