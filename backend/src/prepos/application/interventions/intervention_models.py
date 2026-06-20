from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InterventionScoreBreakdown(BaseModel):
    forecast_risk: float
    weakness: float
    historical_failure: float
    pyq_importance: float
    memory_signal: float
    priority_score: float


class RecommendedInterventionItem(BaseModel):
    id: UUID | None = None
    intervention_type: str
    concept_id: str | None = None
    concept: str | None = None
    predicted_gain: float
    priority_score: float
    impact_score: float
    confidence: str
    reason: str
    forecast_improvement: float = 0.0
    score_breakdown: InterventionScoreBreakdown | None = None


class StudentInterventionResponse(BaseModel):
    student_id: UUID
    exam_id: str
    current_readiness: float | None = None
    forecast_status: str | None = None
    recommended_interventions: list[RecommendedInterventionItem] = Field(default_factory=list)
    active_interventions: list["InterventionRecordResponse"] = Field(default_factory=list)
    generated_at: datetime


class InterventionRecordResponse(BaseModel):
    id: UUID
    mentor_id: UUID
    student_id: UUID
    exam_id: str
    intervention_type: str
    concept_id: str | None
    concept: str | None = None
    reason: str
    predicted_gain: float
    priority_score: float
    status: str
    created_at: datetime


class InterventionExplainResponse(BaseModel):
    intervention_id: UUID
    intervention_type: str
    concept_id: str | None
    concept: str | None = None
    reason: str
    predicted_gain: float
    priority_score: float
    score_breakdown: InterventionScoreBreakdown
    explanations: list[str]


class InterventionHistoryEntry(BaseModel):
    intervention_id: UUID
    intervention_type: str
    concept_id: str | None
    concept: str | None = None
    status: str
    predicted_gain: float
    actual_gain: float | None = None
    effectiveness_score: float | None = None
    created_at: datetime
    evaluated_at: datetime | None = None


class InterventionHistoryResponse(BaseModel):
    interventions: list[InterventionHistoryEntry]
    total: int


class MentorInterventionQueueItem(BaseModel):
    student_id: UUID
    exam_id: str
    top_intervention_type: str
    top_concept: str | None
    priority_score: float
    predicted_gain: float
    forecast_status: str | None
    reason: str


class MentorInterventionQueueResponse(BaseModel):
    items: list[MentorInterventionQueueItem]
    total: int


class InterventionAdminResponse(BaseModel):
    total_interventions: int
    interventions_last_30_days: int
    average_gain: float
    average_effectiveness: float
    mentor_success_rate: float
    top_interventions: list[dict[str, object]]
    least_effective_interventions: list[dict[str, object]]
    status_counts: list[dict[str, object]]


@dataclass(frozen=True, slots=True)
class RankedIntervention:
    intervention_type: str
    concept_id: str | None
    concept_name: str | None
    reason: str
    predicted_gain: float
    priority_score: float
    impact_score: float
    confidence: str
    forecast_improvement: float
    score_breakdown: InterventionScoreBreakdown
