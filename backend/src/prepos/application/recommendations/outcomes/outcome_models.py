from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

OutcomeStatus = Literal["successful", "partial", "failed"]


class RecommendationOutcomeResponse(BaseModel):
    id: UUID
    recommendation_event_id: UUID
    concept_id: str
    concept_name: str
    predicted_gain: float
    actual_gain: float
    effectiveness_score: float
    status: OutcomeStatus
    readiness_before: float | None = None
    readiness_after: float | None = None
    forecast_before: float | None = None
    forecast_after: float | None = None
    weakness_before: float | None = None
    weakness_after: float | None = None
    study_minutes: int = 0
    created_at: datetime


class RecommendationOutcomeListResponse(BaseModel):
    outcomes: list[RecommendationOutcomeResponse]
    total: int


class RecommendationEffectivenessItem(BaseModel):
    concept_id: str
    concept_name: str
    predicted_gain: float
    actual_gain: float
    effectiveness_score: float
    status: OutcomeStatus
    outcome_count: int = 1


class RecommendationEffectivenessResponse(BaseModel):
    average_effectiveness: float
    average_actual_gain: float
    completion_rate: float
    success_rate: float
    items: list[RecommendationEffectivenessItem]


class CompleteRecommendationResponse(BaseModel):
    status: str
    outcome: RecommendationOutcomeResponse | None = None


class RecommendationEffectivenessAdminResponse(BaseModel):
    average_effectiveness: float
    average_actual_gain: float
    completion_rate: float
    success_rate: float
    top_performing_concepts: list[RecommendationEffectivenessItem]
    lowest_performing_concepts: list[RecommendationEffectivenessItem]
    readiness_uplift_trend: list[dict[str, float | str]]
    forecast_uplift_trend: list[dict[str, float | str]]
    concept_rankings: list[RecommendationEffectivenessItem]


class RecommendationEffectivenessMetricRecord(BaseModel):
    tenant_id: UUID
    metric_date: date
    concept_id: str
    recommendation_count: int
    completion_count: int
    average_predicted_gain: float
    average_actual_gain: float
    average_effectiveness: float


class RecommendationCompleteRequest(BaseModel):
    exam_id: str | None = None
    study_minutes: int = Field(default=0, ge=0, le=24 * 60)
    student_id: str | None = None
