from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.common import round_score
from prepos.domain.scoring.predicted_score_v1 import PreparationRisk

PREDICTED_SCORE_EXPLANATIONS_V1 = "predicted_score_explanations_v1"

_LOW_CONFIDENCE_THRESHOLD = Decimal("70")


def _format_score(value: Decimal) -> str:
    return f"{round_score(value):.2f}".rstrip("0").rstrip(".")


def explain_predicted_score_v1(
    *,
    expected_score: Decimal,
    complete_recommendations_score: Decimal,
    confidence_subscore: Decimal | None,
) -> str:
    """Deterministic predicted outcome copy."""
    gain = round_score(complete_recommendations_score - expected_score)
    if gain > Decimal("0"):
        gain_text = _format_score(gain)
        return (
            f"Completing recommended revisions could increase expected score by "
            f"{gain_text} points."
        )

    if confidence_subscore is not None and confidence_subscore < _LOW_CONFIDENCE_THRESHOLD:
        return "Low confidence increases uncertainty in score prediction."

    return f"Current readiness suggests a likely score around {_format_score(expected_score)}."


def explain_risk_level(risk_level: PreparationRisk) -> str:
    if risk_level == PreparationRisk.LOW:
        return "Preparation risk is low based on current readiness."
    if risk_level == PreparationRisk.MEDIUM:
        return "Preparation risk is moderate; targeted study can improve outcomes."
    return "Preparation risk is high; prioritize weak and overdue concepts."
