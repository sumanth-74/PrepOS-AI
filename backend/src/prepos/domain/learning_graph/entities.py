from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ConceptProgressNode:
    id: UUID
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    catalog_version: str
    concept_id: str
    subject_id: str
    topic_id: str
    mastery_score: Decimal
    mastery_nonmcq_score: Decimal
    retention_score: Decimal | None
    confidence_score: Decimal | None
    importance_score: Decimal
    overconfidence_flag: bool
    mcq_attempt_count: int
    mcq_correct_count: int
    nonmcq_attempt_count: int
    revision_count: int
    study_minutes: int
    node_state: str
    mastery_version: str
    mastery_nonmcq_version: str
    retention_version: str
    confidence_version: str
    importance_version: str
    first_seen_at: datetime
    last_activity_at: datetime | None
    row_version: int
    retention_stability_s: Decimal | None = None
    retention_last_event_at: datetime | None = None
    retention_last_review_at: datetime | None = None
    retention_last_grade: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class LearningGraphEvent:
    id: UUID
    tenant_id: UUID
    student_id: UUID
    concept_id: str
    event_type: str
    event_payload: dict[str, object]
    causation_id: str | None
    correlation_id: str
    event_version: int
    occurred_at: datetime
    recorded_at: datetime
    scoring_versions: dict[str, str]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ScoreAuditLog:
    id: UUID
    tenant_id: UUID
    student_id: UUID
    concept_id: str
    score_type: str
    previous_value: Decimal | None
    new_value: Decimal | None
    reason: str
    causation_id: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class StudentGraphSummary:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    total_nodes: int
    active_nodes: int
    average_mastery: Decimal | None
    average_retention: Decimal | None
    average_confidence: Decimal | None
    weakest_concept_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LearningGraphReadinessSnapshot:
    """Readiness Engine input port; retention is materialized at snapshot time."""

    average_mastery: Decimal | None
    average_retention: Decimal | None
    average_confidence: Decimal | None
    rated_node_count: int
    total_node_count: int


@dataclass(frozen=True, slots=True)
class DueRevisionItem:
    student_id: UUID
    concept_id: str
    next_review_at: datetime
    retention_score: Decimal
    importance_score: Decimal
