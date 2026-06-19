from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    target_exam: str | None = Field(default=None, description="Target exam identifier (exam_id).")
    target_year: int | None = None
    daily_study_hours: Decimal | None = None
    experience_level: str | None = None
    onboarding_completed: bool
    onboarding_completed_at: datetime | None = None


class UpdateStudentGoalsRequest(BaseModel):
    target_exam: str | None = Field(default=None, description="Target exam identifier (exam_id).")
    target_year: int | None = None
    daily_study_hours: Decimal | None = Field(default=None, ge=Decimal("0.5"), le=Decimal("16"))
    experience_level: str | None = None


class CompleteOnboardingRequest(BaseModel):
    diagnostic_offered: bool = False


class OnboardingProvisioningResponse(BaseModel):
    learning_graph_provision_id: UUID
    preparation_twin_id: UUID
    expected_node_count: int
    catalog_version: str
    target_stages: list[str]


class CompleteOnboardingResponse(BaseModel):
    student: StudentProfileResponse
    provisioning: OnboardingProvisioningResponse
