from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


SEGMENT_TYPES: frozenset[str] = frozenset(
    {
        "high_performer",
        "on_track",
        "recovering",
        "at_risk",
        "critical_risk",
        "stagnant",
        "high_potential",
        "intervention_responder",
        "intervention_resistant",
    }
)


class CohortMetrics(BaseModel):
    average_readiness: float
    average_forecast: float
    average_gain: float
    goal_attainment_rate: float
    recommendation_effectiveness: float
    planning_adherence: float
    mentor_intervention_success: float
    pyq_preparedness: float
    current_affairs_preparedness: float
    cohort_health_score: float


class StudentSegmentItem(BaseModel):
    student_id: UUID
    segment_type: str
    segment_score: float
    risk_score: float
    readiness: float
    forecast_probability: float
    exam_id: str


class CohortSummaryResponse(BaseModel):
    cohort_id: str
    exam_id: str
    student_count: int
    segments: dict[str, int]
    metrics: CohortMetrics
    top_risks: list[str]
    generated_at: datetime


class CohortStudentsResponse(BaseModel):
    cohort_id: str
    students: list[StudentSegmentItem]
    total: int


class CohortSegmentsResponse(BaseModel):
    cohort_id: str
    distribution: dict[str, int]
    students: list[StudentSegmentItem]
    total: int


class CohortRiskItem(BaseModel):
    student_id: UUID
    risk_score: float
    segment_type: str
    readiness: float
    forecast_probability: float
    top_risk_factors: list[str]


class CohortRisksResponse(BaseModel):
    cohort_id: str
    risks: list[CohortRiskItem]
    top_concept_risks: list[str]
    total: int


class CohortTrendItem(BaseModel):
    concept_id: str
    concept_name: str
    trend_direction: str
    readiness_delta: float
    period: str


class CohortTrendsResponse(BaseModel):
    cohort_id: str
    trends: list[CohortTrendItem]
    readiness_trend: str
    forecast_trend: str
    cohort_growth: float


class MentorComparisonItem(BaseModel):
    mentor_id: str
    intervention_success_rate: float
    student_count: int
    average_gain: float


class CohortAdminResponse(BaseModel):
    total_snapshots: int
    snapshots_last_30_days: int
    total_students_segmented: int
    average_cohort_health: float
    segment_distribution: dict[str, int]
    top_risk_concepts: list[str]
    mentor_comparisons: list[MentorComparisonItem]
    event_counts: list[dict[str, object]]


@dataclass(frozen=True, slots=True)
class StudentCohortInput:
    student_id: UUID
    exam_id: str
    readiness: float
    forecast_probability: float
    projected_readiness: float
    on_track: bool
    goal_attainment: float
    planning_adherence: float
    recommendation_effectiveness: float
    intervention_effectiveness: float
    intervention_count: int
    readiness_delta: float
    weekly_progress: float
    consistency_score: float
    pyq_preparedness: float
    current_affairs_preparedness: float
    negative_drivers: tuple[str, ...]
    failed_intervention_count: int


@dataclass(frozen=True, slots=True)
class SegmentationResult:
    segment_type: str
    segment_score: float
    risk_score: float
    risk_factors: tuple[str, ...]
