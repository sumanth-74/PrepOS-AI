from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DailyPlanItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concept_id: str
    activity_type: str
    estimated_minutes: int
    priority_score: Decimal
    adaptive_priority: Decimal
    readiness_gain: Decimal
    adjustment_explanation: str = ""


class StudyPlanExecutionRequest(BaseModel):
    exam_id: str
    concept_id: str
    activity_type: str
    planned_minutes: int = Field(ge=1)
    actual_minutes: int = Field(ge=0, default=0)


class StudyPlanExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concept_id: str
    status: str
    completed_at: datetime


class WeeklyPlanItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concept_id: str
    target_sessions: int
    estimated_minutes: int
    readiness_gain: Decimal


class StudyPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    generated_at: datetime | None = None
    total_estimated_gain: Decimal = Decimal("0.00")
    daily_plan: list[DailyPlanItemResponse] = Field(default_factory=list)
    weekly_plan: list[WeeklyPlanItemResponse] = Field(default_factory=list)
