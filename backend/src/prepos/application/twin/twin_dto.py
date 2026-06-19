from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TwinGoalSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_readiness_score: Decimal | None = None
    target_date: date | None = None


class TwinMentorCaseSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_status: str | None = None
    priority: str | None = None
    opened_at: datetime | None = None


class TwinMentorEffectivenessSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    best_action: str | None = None
    effectiveness_score: Decimal | None = None
    sample_size: int | None = None


class TwinProjectionMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rebuild_count: int = 0
    skipped_rebuild_count: int = 0
    incremental_update_count: int = 0
    lock_contention_count: int = 0


class TwinDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    readiness_score: Decimal | None = None
    due_revision_count: int = 0
    high_risk_concept_count: int = 0
    recommendation_count: int = 0
    largest_positive_driver: str | None = None
    largest_negative_driver: str | None = None
    top_positive_drivers: list[str] = Field(default_factory=list)
    top_negative_drivers: list[str] = Field(default_factory=list)
    total_estimated_gain: Decimal | None = None
    today_plan_count: int = 0
    weekly_plan_count: int = 0
    completion_rate: Decimal | None = None
    skip_rate: Decimal | None = None
    projected_readiness: Decimal | None = None
    gap_to_goal: Decimal | None = None
    on_track: bool | None = None
    expected_score: Decimal | None = None
    low_score: Decimal | None = None
    high_score: Decimal | None = None
    risk_level: str | None = None
    milestone_status: str | None = None
    expected_weekly_progress: Decimal | None = None
    next_milestone_date: date | None = None
    next_milestone_target: Decimal | None = None
    goal_probability: Decimal | None = None
    goal_likelihood: str | None = None
    best_case_readiness: Decimal | None = None
    worst_case_readiness: Decimal | None = None
    current_decision: str | None = None
    expected_readiness_gain: Decimal | None = None
    expected_score_gain: Decimal | None = None
    current_intervention: str | None = None
    intervention_urgency: str | None = None
    intervention_score: Decimal | None = None
    best_intervention: str | None = None
    historical_effectiveness: Decimal | None = None
    last_effectiveness_score: Decimal | None = None
    learning_style: str | None = None
    risk_profile: str | None = None
    consistency_score: Decimal | None = None
    best_activity_type: str | None = None
    top_multiplier: Decimal | None = None
    mentor_status: str | None = None
    top_mentor_message: str | None = None
    mentor_action: str | None = None
    mentor_action_priority: Decimal | None = None
    escalation_level: str | None = None
    goal_summary: TwinGoalSummaryResponse | None = None
    mentor_case: TwinMentorCaseSummaryResponse | None = None
    mentor_effectiveness: TwinMentorEffectivenessSummaryResponse | None = None
    generated_at: datetime | None = None


class TwinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_version: str
    projection_version: int = 0
    readiness_score: Decimal | None = None
    average_mastery: Decimal | None = None
    average_retention: Decimal | None = None
    average_confidence: Decimal | None = None
    rated_node_count: int = 0
    due_revision_count: int = 0
    high_risk_concept_count: int = 0
    largest_positive_driver: str | None = None
    largest_negative_driver: str | None = None
    recommendation_count: int = 0
    last_recommendation_at: datetime | None = None
    total_estimated_gain: Decimal | None = None
    predicted_outcome: dict[str, object] | None = None
    simulations: dict[str, object] | None = None
    decision: dict[str, object] | None = None
    intervention: dict[str, object] | None = None
    intervention_effectiveness: dict[str, object] | None = None
    optimization: dict[str, object] | None = None
    behavior_profile: dict[str, object] | None = None
    personalization: dict[str, object] | None = None
    mentor: dict[str, object] | None = None
    mentor_action: dict[str, object] | None = None
    escalation: dict[str, object] | None = None
    twin_payload: dict[str, object] = Field(default_factory=dict)
    generated_at: datetime | None = None
