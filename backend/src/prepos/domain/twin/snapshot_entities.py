from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PreparationTwin:
    id: UUID
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    profile_version: str
    readiness_score: Decimal | None
    average_mastery: Decimal | None
    average_retention: Decimal | None
    average_confidence: Decimal | None
    rated_node_count: int
    due_revision_count: int
    high_risk_concept_count: int
    largest_positive_driver: str | None
    largest_negative_driver: str | None
    recommendation_count: int
    last_recommendation_at: datetime | None
    twin_payload: dict[str, object]
    generated_at: datetime
    projection_revision: int = 0
    last_learning_graph_version: int | None = None
    rebuild_count: int = 0
    skipped_rebuild_count: int = 0
    incremental_update_count: int = 0
    lock_contention_count: int = 0
    decision_type: str | None = None
    decision_score: Decimal | None = None
    expected_readiness_gain: Decimal | None = None
    expected_score_gain: Decimal | None = None
    intervention_type: str | None = None
    intervention_score: Decimal | None = None
    intervention_urgency: str | None = None
    learning_style: str | None = None
    risk_profile: str | None = None
    consistency_score: Decimal | None = None
    discipline_score: Decimal | None = None
    engagement_score: Decimal | None = None
    best_activity_type: str | None = None
    top_multiplier: Decimal | None = None
    historical_effectiveness: Decimal | None = None
    mentor_status: str | None = None
    top_mentor_message: str | None = None
    mentor_action_type: str | None = None
    mentor_action_priority: Decimal | None = None
    escalation_level: str | None = None
    active_case_status: str | None = None
    active_case_priority: str | None = None


# Backward-compatible alias for S5.5 snapshot naming.
TwinSnapshot = PreparationTwin
