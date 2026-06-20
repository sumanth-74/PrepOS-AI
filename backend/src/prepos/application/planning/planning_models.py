from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlanningScoreBreakdown(BaseModel):
    weakness_score: float
    recommendation_impact_score: float
    pyq_frequency_score: float
    forecast_risk_score: float
    current_affairs_score: float
    memory_success_score: float
    priority_score: float
    reason_codes: list[str] = Field(default_factory=list)


class PlanItemResponse(BaseModel):
    id: UUID
    concept_id: str
    concept_name: str
    activity_type: str
    priority_score: float
    estimated_minutes: int
    estimated_readiness_gain: float
    confidence: str
    scheduled_date: date
    source_reason: str
    completion_status: str


class PlanRevisionResponse(BaseModel):
    id: UUID
    concept_id: str
    revision_reason: str
    old_priority: float | None
    new_priority: float | None
    created_at: datetime


class AdaptivePlanResponse(BaseModel):
    plan_id: UUID
    exam_id: str
    generated_at: datetime
    valid_from: date
    valid_to: date
    readiness_snapshot: float | None
    forecast_snapshot: float | None
    status: str
    today_items: list[PlanItemResponse]
    week_items: list[PlanItemResponse]
    next_week_draft: list[PlanItemResponse]
    total_estimated_gain: float
    daily_minutes_budget: int


class PlanHistoryEntry(BaseModel):
    plan_id: UUID
    generated_at: datetime
    valid_from: date
    valid_to: date
    status: str
    item_count: int
    completed_count: int


class PlanHistoryResponse(BaseModel):
    plans: list[PlanHistoryEntry]
    total: int


class PlanCompletionResponse(BaseModel):
    item_id: UUID
    concept_id: str
    completion_status: str
    estimated_readiness_gain: float


class PlanExplainResponse(BaseModel):
    concept_id: str
    concept_name: str
    priority_score: float
    estimated_readiness_gain: float
    estimated_minutes: int
    confidence: str
    source_reason: str
    score_breakdown: PlanningScoreBreakdown
    explanations: list[str]


class PlanningAdminResponse(BaseModel):
    total_plans: int
    active_plans: int
    plans_generated_last_30_days: int
    average_completion_rate: float
    average_adherence: float
    top_scheduled_concepts: list[dict[str, object]]
    event_counts: list[dict[str, object]]
