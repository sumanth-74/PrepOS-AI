from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.common import round_score

FORECAST_EXPLANATIONS_V1 = "forecast_explanations_v1"


def _format_score(value: Decimal) -> str:
    return f"{round_score(value):.2f}".rstrip("0").rstrip(".")


def explain_forecast_v1(
    *,
    projected_readiness: Decimal,
    target_readiness_score: Decimal,
    on_track: bool,
    gap_to_goal: Decimal,
    base_capacity_minutes: int,
    adaptive_capacity_minutes: int,
) -> str:
    """Deterministic trajectory copy for Twin and dashboard."""
    if on_track and gap_to_goal == Decimal("0") and projected_readiness >= target_readiness_score:
        return "Current trajectory exceeds your target."

    if adaptive_capacity_minutes > base_capacity_minutes:
        delta = adaptive_capacity_minutes - base_capacity_minutes
        return f"Increase study time by {delta} minutes/day to stay on track."

    return f"You are projected to reach {_format_score(projected_readiness)} readiness before the exam."
