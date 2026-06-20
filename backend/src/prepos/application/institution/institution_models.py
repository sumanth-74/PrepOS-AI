from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


INSIGHT_TYPES: frozenset[str] = frozenset(
    {
        "concept_weakness",
        "mentor_outperformance",
        "readiness_drop",
        "forecast_decline",
        "current_affairs_drop",
        "pyq_gain_signal",
        "intervention_underperformance",
        "cohort_risk_spike",
    }
)

RECOMMENDATION_TYPES: frozenset[str] = frozenset(
    {
        "assign_mentor_capacity",
        "create_revision_campaign",
        "increase_current_affairs_sessions",
        "review_weak_concepts",
        "launch_intervention_program",
        "review_intervention_strategy",
    }
)


class InstitutionEvidence(BaseModel):
    label: str
    value: str


class InstitutionInsightItem(BaseModel):
    insight_type: str
    insight_key: str
    title: str
    severity: str
    evidence: list[InstitutionEvidence]
    calculation: str
    source_metrics: dict[str, float | int | str]


class InstitutionInsightsResponse(BaseModel):
    insights: list[InstitutionInsightItem]
    total: int
    generated_at: datetime


class InstitutionRecommendationItem(BaseModel):
    recommendation_type: str
    title: str
    expected_impact: float
    affected_students: int
    affected_cohorts: list[str]
    explanation: str
    priority_score: float


class InstitutionRecommendationsResponse(BaseModel):
    recommendations: list[InstitutionRecommendationItem]
    total: int
    generated_at: datetime


class InstitutionTrendItem(BaseModel):
    trend_type: str
    trend_key: str
    trend_direction: str
    delta_value: float
    period: str
    label: str


class InstitutionTrendsResponse(BaseModel):
    trends: list[InstitutionTrendItem]
    readiness_trend: str
    forecast_trend: str
    intervention_roi: float
    generated_at: datetime


class MentorEffectivenessItem(BaseModel):
    mentor_id: str
    intervention_success_rate: float
    student_count: int
    average_gain: float
    cohort_average_success_rate: float
    outperformance_pct: float


class InstitutionMentorEffectivenessResponse(BaseModel):
    mentors: list[MentorEffectivenessItem]
    cohort_average_success_rate: float
    total: int
    generated_at: datetime


class CohortComparisonItem(BaseModel):
    cohort_id: str
    exam_id: str
    student_count: int
    average_readiness: float
    average_forecast: float
    cohort_health_score: float
    at_risk_count: int


class InstitutionKpis(BaseModel):
    total_students: int
    total_cohorts: int
    average_readiness: float
    average_forecast: float
    average_cohort_health: float
    at_risk_students: int
    intervention_roi: float
    institution_health_score: float


class InstitutionDashboardResponse(BaseModel):
    kpis: InstitutionKpis
    cohort_comparisons: list[CohortComparisonItem]
    weak_concepts: list[str]
    top_insights: list[InstitutionInsightItem]
    top_recommendations: list[InstitutionRecommendationItem]
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class CohortSnapshotInput:
    cohort_id: str
    exam_id: str
    student_count: int
    avg_readiness: float
    avg_forecast: float
    avg_effectiveness: float
    risk_count: int
    segment_counts: dict[str, int]
    top_risks: tuple[str, ...]
    cohort_health_score: float
    current_affairs_preparedness: float
    pyq_preparedness: float
    snapshot_date: date


@dataclass(frozen=True, slots=True)
class MentorEffectivenessInput:
    mentor_id: str
    intervention_success_rate: float
    student_count: int
    average_gain: float


@dataclass(frozen=True, slots=True)
class InstitutionDataInput:
    cohorts: tuple[CohortSnapshotInput, ...]
    mentors: tuple[MentorEffectivenessInput, ...]
    concept_cohort_counts: dict[str, int]
    previous_readiness_avg: float | None
    current_readiness_avg: float
    previous_forecast_avg: float | None
    current_forecast_avg: float
    previous_ca_avg: float | None
    current_ca_avg: float
    intervention_roi: float
    pyq_gain_signal: float
    total_at_risk: int
