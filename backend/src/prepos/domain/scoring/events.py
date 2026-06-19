from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.scoring.forecast_probability_v1 import GoalLikelihood
from prepos.domain.scoring.predicted_score_v1 import PreparationRisk


@dataclass(frozen=True, slots=True)
class PredictedScoreUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    expected_score: Decimal
    low_score: Decimal
    high_score: Decimal
    risk_level: PreparationRisk
    current_state: Decimal
    complete_recommendations: Decimal
    no_study: Decimal
    explanation: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "PredictedScoreUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "expected_score": float(self.expected_score),
            "low_score": float(self.low_score),
            "high_score": float(self.high_score),
            "risk_level": self.risk_level.value,
            "current_state": float(self.current_state),
            "complete_recommendations": float(self.complete_recommendations),
            "no_study": float(self.no_study),
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class ForecastProbabilityUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    goal_probability: Decimal
    goal_likelihood: GoalLikelihood
    best_case: Decimal
    expected: Decimal
    worst_case: Decimal
    optimistic_score: Decimal
    expected_score: Decimal
    pessimistic_score: Decimal
    explanation: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "ForecastProbabilityUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "goal_probability": float(self.goal_probability),
            "goal_likelihood": self.goal_likelihood.value,
            "best_case": float(self.best_case),
            "expected": float(self.expected),
            "worst_case": float(self.worst_case),
            "optimistic_score": float(self.optimistic_score),
            "expected_score": float(self.expected_score),
            "pessimistic_score": float(self.pessimistic_score),
            "explanation": self.explanation,
        }
