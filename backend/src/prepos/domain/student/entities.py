from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.student.value_objects import ExperienceLevel, ProvisionStatus, TwinStatus


@dataclass(frozen=True, slots=True)
class Student:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    target_exam_id: str | None
    target_year: int | None
    daily_study_hours: Decimal | None
    experience_level: ExperienceLevel | None
    onboarding_completed: bool
    onboarding_completed_at: datetime | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class LearningGraphProvision:
    id: UUID
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    catalog_version: str
    status: ProvisionStatus
    expected_node_count: int
    provisioned_node_count: int
    provisioned_at: datetime | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PreparationTwinProvision:
    id: UUID
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    status: TwinStatus
    academic_profile: dict[str, object]
    behavioral_profile: dict[str, object]
    prediction_profile: dict[str, object]
    metadata: dict[str, object]
    projection_version: str
    row_version: int
    last_rebuilt_at: datetime
    last_event_id_processed: UUID | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
