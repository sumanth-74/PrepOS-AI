from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ForecastScenarioResponse(BaseModel):
    id: UUID
    scenario_type: str
    scenario_name: str
    weekly_minutes: int
    projected_readiness: float
    projected_score: float | None
    probability_of_success: float


class GoalForecastResponse(BaseModel):
    forecast_id: UUID
    exam_id: str
    forecast_date: date
    target_date: date
    current_readiness: float
    projected_readiness: float
    target_readiness: float
    probability_of_success: float
    forecast_status: str
    top_drivers: list[str] = Field(default_factory=list)
    scenarios: list[ForecastScenarioResponse] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)
    generated_at: datetime


class ForecastHistoryEntry(BaseModel):
    forecast_id: UUID
    forecast_date: date
    projected_readiness: float
    probability_of_success: float
    forecast_status: str
    created_at: datetime


class ForecastHistoryResponse(BaseModel):
    forecasts: list[ForecastHistoryEntry]
    total: int


class CustomScenarioRequest(BaseModel):
    exam_id: str = "upsc_cse"
    weekly_minutes: int = Field(ge=60, le=2520)


class ForecastExplainResponse(BaseModel):
    current_readiness: float
    projected_readiness: float
    target_readiness: float
    probability_of_success: float
    forecast_status: str
    top_drivers: list[str]
    explanations: list[str]
    weekly_gain: float
    adherence_rate: float
    effectiveness_multiplier: float


class ForecastAdminResponse(BaseModel):
    total_forecasts: int
    forecasts_last_30_days: int
    average_probability: float
    on_track_rate: float
    average_projected_gain: float
    scenario_usage: list[dict[str, object]]
    event_counts: list[dict[str, object]]
