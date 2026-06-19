from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TwinRecommendation:
    concept_id: str
    recommendation_type: str
    recommendation_score: Decimal
    importance_score: Decimal
    weakness_score: Decimal
    retention_score: Decimal | None
    readiness_gain: Decimal
    explanation: str


@dataclass(frozen=True, slots=True)
class PersistedTwinRecommendation:
    id: UUID
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    concept_id: str
    recommendation_type: str
    recommendation_score: Decimal
    readiness_gain: Decimal
    created_at: datetime
