from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

RecommendationConfidence = Literal["high", "medium", "low"]


class RecommendationExplainScoreBreakdown(BaseModel):
    weakness: float
    pyq: float
    forecast: float
    current_affairs: float


class ConceptRecommendation(BaseModel):
    concept_id: str
    concept_name: str
    impact_score: float
    reason_codes: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    estimated_readiness_gain: float
    confidence: RecommendationConfidence


class RecommendationExplainResponse(BaseModel):
    concept_id: str
    concept_name: str
    impact_score: float
    weakness_score: float
    pyq_frequency_score: float
    forecast_gain_score: float
    current_affairs_score: float
    reason_codes: list[str]
    reasons: list[str]
    estimated_readiness_gain: float
    confidence: RecommendationConfidence
    score_breakdown: RecommendationExplainScoreBreakdown | None = None
    historical_effectiveness: float | None = None
    average_actual_gain: float | None = None


class StudentRecommendationsRequest(BaseModel):
    exam_id: str | None = None
    limit: int = Field(default=5, ge=1, le=20)


class MentorRecommendationsRequest(BaseModel):
    student_id: str
    exam_id: str | None = None
    limit: int = Field(default=5, ge=1, le=20)


class RecommendationsResponse(BaseModel):
    recommendations: list[ConceptRecommendation]
    generated_at: str


class RecommendationAnalyticsResponse(BaseModel):
    recommendation_acceptance_rate: float
    completion_rate: float
    average_readiness_gain: float
    top_recommended_concepts: list[dict[str, object]]
    recommendation_effectiveness: float
