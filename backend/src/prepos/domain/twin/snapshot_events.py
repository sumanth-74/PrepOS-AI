from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TwinSnapshotUpdated:
    """Deprecated: use TwinUpdated for new integrations."""

    tenant_id: UUID
    student_id: UUID
    exam_id: str
    readiness_score: Decimal | None
    due_revision_count: int
    high_risk_concept_count: int
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "TwinSnapshotUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "readiness_score": float(self.readiness_score) if self.readiness_score is not None else None,
            "due_revision_count": self.due_revision_count,
            "high_risk_concept_count": self.high_risk_concept_count,
        }
