from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConceptProgressNodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concept_id: str
    exam_id: str
    subject_id: str
    topic_id: str
    mastery_score: Decimal
    mastery_nonmcq_score: Decimal
    retention_score: Decimal | None = None
    confidence_score: Decimal | None = None
    importance_score: Decimal
    overconfidence_flag: bool
    mcq_attempt_count: int
    mcq_correct_count: int
    nonmcq_attempt_count: int
    revision_count: int
    study_minutes: int
    node_state: str
    row_version: int
    last_activity_at: datetime | None = None
    retention_stability_s: Decimal | None = None
    retention_last_event_at: datetime | None = None
    retention_last_review_at: datetime | None = None
    retention_last_grade: int | None = None
    next_review_at: datetime | None = None


class LearningGraphOverviewResponse(BaseModel):
    student_id: UUID
    exam_id: str
    total_nodes: int
    provisioned_nodes: int
    expected_nodes: int
    provision_status: str
    nodes: list[ConceptProgressNodeResponse] = Field(default_factory=list)


class LearningGraphSummaryResponse(BaseModel):
    student_id: UUID
    exam_id: str
    total_nodes: int
    active_nodes: int
    average_mastery: Decimal | None = None
    average_retention: Decimal | None = None
    average_confidence: Decimal | None = None


class WeaknessItemResponse(BaseModel):
    concept_id: str
    mastery_score: Decimal
    retention_score: Decimal | None = None
    importance_score: Decimal
    weakness_score: Decimal


class LearningGraphWeaknessesResponse(BaseModel):
    student_id: UUID
    weaknesses: list[WeaknessItemResponse]


class LearningGraphReadinessSnapshotResponse(BaseModel):
    student_id: UUID
    average_mastery: Decimal | None = None
    average_retention: Decimal | None = None
    average_confidence: Decimal | None = None
    rated_node_count: int
    total_node_count: int


class DueRevisionItemResponse(BaseModel):
    concept_id: str
    next_review_at: datetime
    retention_score: Decimal
    importance_score: Decimal


class LearningGraphReadinessResponse(BaseModel):
    version: str
    overall_score: Decimal | None = None
    knowledge_subscore: Decimal | None = None
    retention_subscore: Decimal | None = None
    confidence_subscore: Decimal | None = None
    coverage_subscore: Decimal | None = None
    rated_node_count: int
    total_node_count: int
    unrated: bool
    readiness_score: Decimal | None = Field(
        default=None,
        deprecated=True,
        description="Deprecated alias of overall_score for backward compatibility.",
    )


class RecordAssessmentRequest(BaseModel):
    concept_id: str
    exam_id: str
    mcq_correct: bool
    self_confidence: Decimal | None = None


class RecordRevisionRequest(BaseModel):
    concept_id: str
    exam_id: str
    recall_grade: str = "good"


class RecordStudySessionRequest(BaseModel):
    concept_id: str
    exam_id: str
    engaged_minutes: int = Field(ge=1, le=480)


class RecordPyqChangeRequest(BaseModel):
    concept_id: str
    exam_id: str
    global_importance: Decimal = Field(ge=0, le=100)


class LearningGraphActivityResponse(BaseModel):
    accepted: bool = True
    event_type: str
