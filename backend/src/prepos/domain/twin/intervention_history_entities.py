from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StudentInterventionHistoryEntry:
    id: UUID
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    intervention_type: str
    effectiveness_score: Decimal
    readiness_delta: Decimal
    predicted_score_delta: Decimal
    completion_delta: Decimal
    outcome_status: str
    created_at: datetime
