from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.study_plan.value_objects import ActivityType


@dataclass(frozen=True, slots=True)
class StudyPlanUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    daily_item_count: int
    weekly_item_count: int
    total_estimated_gain: Decimal
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "StudyPlanUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "daily_item_count": self.daily_item_count,
            "weekly_item_count": self.weekly_item_count,
            "total_estimated_gain": float(self.total_estimated_gain),
        }


@dataclass(frozen=True, slots=True)
class StudyPlanItemCompleted:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    concept_id: str
    activity_type: ActivityType
    planned_minutes: int
    actual_minutes: int
    completed_at: datetime
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "StudyPlanItemCompleted"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "concept_id": self.concept_id,
            "activity_type": self.activity_type.value,
            "planned_minutes": self.planned_minutes,
            "actual_minutes": self.actual_minutes,
            "completed_at": self.completed_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class StudyPlanItemSkipped:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    concept_id: str
    activity_type: ActivityType
    planned_minutes: int
    actual_minutes: int
    completed_at: datetime
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "StudyPlanItemSkipped"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "concept_id": self.concept_id,
            "activity_type": self.activity_type.value,
            "planned_minutes": self.planned_minutes,
            "actual_minutes": self.actual_minutes,
            "completed_at": self.completed_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class StudyBehaviorUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    completion_rate: Decimal
    skip_rate: Decimal
    average_minutes_variance: Decimal
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "StudyBehaviorUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "completion_rate": float(self.completion_rate),
            "skip_rate": float(self.skip_rate),
            "average_minutes_variance": float(self.average_minutes_variance),
        }
