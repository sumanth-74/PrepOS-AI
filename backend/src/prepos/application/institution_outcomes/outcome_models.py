from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


INITIATIVE_TYPES: frozenset[str] = frozenset(
    {
        "revision_campaign",
        "mentor_training",
        "current_affairs_boost",
        "forecast_recovery",
        "weak_concept_program",
        "pyq_focus_program",
    }
)

INITIATIVE_STATUSES: frozenset[str] = frozenset({"active", "completed", "cancelled"})
EFFECTIVENESS_STATUSES: frozenset[str] = frozenset({"succeeded", "failed", "partial"})


class CreateInitiativeRequest(BaseModel):
    initiative_type: str
    title: str
    start_date: date
    end_date: date | None = None
    affected_students: int = Field(ge=0)
    affected_cohorts: list[str] = Field(default_factory=list)
    expected_readiness_gain: float = Field(default=5.0, ge=0)
    expected_forecast_gain: float = Field(default=3.0, ge=0)
    expected_cohort_health_gain: float = Field(default=4.0, ge=0)
    expected_risk_reduction: int = Field(default=5, ge=0)


class InitiativeItem(BaseModel):
    id: UUID
    initiative_type: str
    title: str
    status: str
    start_date: date
    end_date: date | None
    affected_students: int
    affected_cohorts: list[str]
    expected_outcomes: dict[str, float | int]
    actual_outcomes: dict[str, float | int]
    created_at: datetime


class InitiativesResponse(BaseModel):
    initiatives: list[InitiativeItem]
    total: int


class OutcomeState(BaseModel):
    readiness: float
    forecast: float
    cohort_health: float
    risk_count: int


class OutcomeItem(BaseModel):
    initiative_id: UUID | None
    outcome_type: str
    subject_key: str
    before: OutcomeState
    after: OutcomeState
    actual_gain: float
    expected_gain: float
    variance: float
    readiness_gain: float
    forecast_gain: float
    cohort_health_gain: float
    risk_reduction: float


class OutcomesResponse(BaseModel):
    outcomes: list[OutcomeItem]
    total: int
    average_readiness_uplift: float
    average_forecast_uplift: float
    average_risk_reduction: float
    generated_at: datetime


class RoiEvidence(BaseModel):
    label: str
    value: str


class RoiItem(BaseModel):
    initiative_id: UUID | None
    subject_key: str
    initiative_type: str | None
    title: str | None
    roi_score: float
    readiness_gain: float
    forecast_gain: float
    cohort_health_gain: float
    risk_reduction: float
    evidence: list[RoiEvidence]
    calculation: str


class RoiResponse(BaseModel):
    items: list[RoiItem]
    total: int
    average_roi_score: float
    best_initiatives: list[RoiItem]
    failed_initiatives: list[RoiItem]
    generated_at: datetime


class InitiativeEffectivenessItem(BaseModel):
    initiative_id: UUID
    initiative_type: str
    title: str
    effectiveness_score: float
    readiness_delta: float
    forecast_delta: float
    cohort_health_delta: float
    risk_reduction: int
    roi_score: float
    status: str


class InitiativeEffectivenessResponse(BaseModel):
    items: list[InitiativeEffectivenessItem]
    total: int
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class MetricSnapshot:
    readiness: float
    forecast: float
    cohort_health: float
    risk_count: int


@dataclass(frozen=True, slots=True)
class InitiativeInput:
    initiative_id: UUID
    initiative_type: str
    title: str
    status: str
    affected_students: int
    affected_cohorts: tuple[str, ...]
    before: MetricSnapshot
    after: MetricSnapshot
    expected_readiness_gain: float
    expected_forecast_gain: float
    expected_cohort_health_gain: float
    expected_risk_reduction: int
