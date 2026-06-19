from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile
from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.decision_types_v1 import TwinDecisionType
from prepos.domain.twin.intervention_outcome_types_v1 import InterventionOutcomeStatus
from prepos.domain.twin.intervention_types_v1 import InterventionUrgency, TwinInterventionType


@dataclass(frozen=True, slots=True)
class TwinDecisionUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    decision_type: TwinDecisionType
    decision_score: Decimal
    expected_readiness_gain: Decimal
    expected_score_gain: Decimal
    explanation: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "TwinDecisionUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "decision_type": self.decision_type.value,
            "decision_score": float(self.decision_score),
            "expected_readiness_gain": float(self.expected_readiness_gain),
            "expected_score_gain": float(self.expected_score_gain),
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class TwinInterventionUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    intervention_type: TwinInterventionType
    intervention_score: Decimal
    urgency: InterventionUrgency
    expected_readiness_gain: Decimal
    title: str
    description: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "TwinInterventionUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "intervention_type": self.intervention_type.value,
            "intervention_score": float(self.intervention_score),
            "urgency": self.urgency.value,
            "expected_readiness_gain": float(self.expected_readiness_gain),
            "title": self.title,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class InterventionOutcomeCalculated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    intervention_type: TwinInterventionType
    effectiveness_score: Decimal
    readiness_delta: Decimal
    predicted_score_delta: Decimal
    completion_delta: Decimal
    outcome_status: InterventionOutcomeStatus
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "InterventionOutcomeCalculated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "intervention_type": self.intervention_type.value,
            "effectiveness_score": float(self.effectiveness_score),
            "readiness_delta": float(self.readiness_delta),
            "predicted_score_delta": float(self.predicted_score_delta),
            "completion_delta": float(self.completion_delta),
            "outcome_status": self.outcome_status.value,
        }


@dataclass(frozen=True, slots=True)
class InterventionOptimizationUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    best_intervention: str
    historical_effectiveness: Decimal
    last_effectiveness_score: Decimal
    outcome_status: str
    optimized_intervention_score: Decimal
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "InterventionOptimizationUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "best_intervention": self.best_intervention,
            "historical_effectiveness": float(self.historical_effectiveness),
            "last_effectiveness_score": float(self.last_effectiveness_score),
            "outcome_status": self.outcome_status,
            "optimized_intervention_score": float(self.optimized_intervention_score),
        }


@dataclass(frozen=True, slots=True)
class BehaviorProfileUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    consistency_score: Decimal
    discipline_score: Decimal
    revision_adherence_score: Decimal
    weakness_recovery_score: Decimal
    engagement_score: Decimal
    learning_style: LearningStyle
    risk_profile: RiskProfile
    explanation: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "BehaviorProfileUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "consistency_score": float(self.consistency_score),
            "discipline_score": float(self.discipline_score),
            "revision_adherence_score": float(self.revision_adherence_score),
            "weakness_recovery_score": float(self.weakness_recovery_score),
            "engagement_score": float(self.engagement_score),
            "learning_style": self.learning_style.value,
            "risk_profile": self.risk_profile.value,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class PersonalizationUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    learning_style: LearningStyle
    risk_profile: RiskProfile
    top_multiplier: Decimal
    best_activity_type: ActivityType
    historical_effectiveness: Decimal
    explanation: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "PersonalizationUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "learning_style": self.learning_style.value,
            "risk_profile": self.risk_profile.value,
            "top_multiplier": float(self.top_multiplier),
            "best_activity_type": self.best_activity_type.value,
            "historical_effectiveness": float(self.historical_effectiveness),
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class TwinRecommendationsUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    recommendation_count: int
    concept_ids: tuple[str, ...]
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "TwinRecommendationsUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "recommendation_count": self.recommendation_count,
            "concept_ids": list(self.concept_ids),
        }
