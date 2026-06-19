from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.learning_graph.value_objects import DEFAULT_NODE_SCORING_VERSIONS


@dataclass(frozen=True, slots=True)
class LearningGraphUpdated:
    tenant_id: UUID
    student_id: UUID
    concept_id: str
    exam_id: str
    mastery_score: Decimal
    mastery_nonmcq_score: Decimal
    retention_score: Decimal | None
    confidence_score: Decimal | None
    importance_score: Decimal
    overconfidence_flag: bool
    node_state: str
    row_version: int
    changed_scores: tuple[str, ...]
    scoring_versions: dict[str, str]
    causation_id: str | None
    correlation_id: str
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "LearningGraphUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "concept_id": self.concept_id,
            "exam_id": self.exam_id,
            "changed_scores": list(self.changed_scores),
            "mastery_score": float(self.mastery_score),
            "mastery_nonmcq_score": float(self.mastery_nonmcq_score),
            "retention_score": float(self.retention_score) if self.retention_score is not None else None,
            "confidence_score": float(self.confidence_score) if self.confidence_score is not None else None,
            "importance_score": float(self.importance_score),
            "overconfidence_flag": self.overconfidence_flag,
            "node_state": self.node_state,
            "row_version": self.row_version,
            "scoring_versions": dict(self.scoring_versions or DEFAULT_NODE_SCORING_VERSIONS),
        }


@dataclass(frozen=True, slots=True)
class AssessmentCompleted:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    concept_id: str
    mcq_correct: bool
    self_confidence: float | None
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "AssessmentCompleted"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "concept_id": self.concept_id,
            "mcq_correct": self.mcq_correct,
            "self_confidence": self.self_confidence,
        }


@dataclass(frozen=True, slots=True)
class RevisionCompleted:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    concept_id: str
    recall_grade: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "RevisionCompleted"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "concept_id": self.concept_id,
            "recall_grade": self.recall_grade,
        }


@dataclass(frozen=True, slots=True)
class StudySessionLogged:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    concept_id: str
    engaged_minutes: int
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "StudySessionLogged"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "concept_id": self.concept_id,
            "engaged_minutes": self.engaged_minutes,
        }


@dataclass(frozen=True, slots=True)
class PYQDataChanged:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    concept_id: str
    global_importance: float
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "PYQDataChanged"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "concept_id": self.concept_id,
            "global_importance": self.global_importance,
        }
