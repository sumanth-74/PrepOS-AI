from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.common import round_score

FORECAST_PROBABILITY_EXPLANATIONS_V1 = "forecast_probability_explanations_v1"

_LOW_CONFIDENCE_THRESHOLD = Decimal("70")


def _format_score(value: Decimal) -> str:
    return f"{round_score(value):.2f}".rstrip("0").rstrip(".")


def explain_forecast_probability_v1(
    *,
    goal_probability: Decimal,
    confidence_subscore: Decimal | None,
    total_estimated_gain: Decimal,
) -> str:
    """Deterministic probabilistic forecast copy."""
    if confidence_subscore is not None and confidence_subscore < _LOW_CONFIDENCE_THRESHOLD:
        return "Low confidence increases forecast uncertainty."

    if total_estimated_gain > Decimal("0"):
        gain = _format_score(total_estimated_gain)
        return f"Completing all planned revisions could improve readiness by {gain} points."

    probability = _format_score(goal_probability)
    return f"You currently have a {probability}% likelihood of reaching your goal."
