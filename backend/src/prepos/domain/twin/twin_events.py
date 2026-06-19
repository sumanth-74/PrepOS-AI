from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1


@dataclass(frozen=True, slots=True)
class TwinUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    profile_version: str
    generated_at: datetime
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "TwinUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "profile_version": self.profile_version or TWIN_PROFILE_V1,
            "generated_at": self.generated_at.isoformat(),
        }
