from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StudentOnboardingCompleted:
    student_id: UUID
    user_id: UUID
    tenant_id: UUID
    exam_id: str
    diagnostic_offered: bool
    target_stages: tuple[str, ...]
    catalog_version: str
    occurred_at: datetime
    correlation_id: str
    causation_id: str | None = None

    @property
    def event_type(self) -> str:
        return "StudentOnboardingCompleted"

    def to_payload(self) -> dict[str, object]:
        return {
            "student_id": str(self.student_id),
            "user_id": str(self.user_id),
            "tenant_id": str(self.tenant_id),
            "exam_id": self.exam_id,
            "diagnostic_offered": self.diagnostic_offered,
            "target_stages": list(self.target_stages),
            "catalog_version": self.catalog_version,
        }
