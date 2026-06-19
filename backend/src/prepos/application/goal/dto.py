from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GoalTrajectoryResponse(BaseModel):
    required_gain: Decimal
    expected_daily_progress: Decimal
    expected_weekly_progress: Decimal


class GoalMilestoneResponse(BaseModel):
    target_date: date
    target_readiness: Decimal
    expected_score: Decimal


class GoalUpsertRequest(BaseModel):
    exam_id: str
    target_readiness_score: Decimal = Field(ge=Decimal("0"), le=Decimal("100"))
    target_date: date
    daily_capacity_minutes: int = Field(default=120, ge=30, le=300)


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exam_id: str
    target_readiness_score: Decimal
    target_date: date
    daily_capacity_minutes: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    trajectory: GoalTrajectoryResponse | None = None
    milestones: list[GoalMilestoneResponse] = Field(default_factory=list)
    goal_probability: Decimal | None = None
    goal_likelihood: str | None = None
