from __future__ import annotations

from prepos.application.forecasting.goal_forecasting_engine import ForecastEngineResult


def explain_forecast(
    *,
    result: ForecastEngineResult,
    target_readiness: float,
    top_drivers: list[str],
    adherence_rate: float,
    effectiveness_multiplier: float,
) -> list[str]:
    lines = [
        (
            f"Projected readiness {result.projected_readiness:.1f} from current "
            f"{result.projected_readiness - result.expected_gain:.1f} with expected gain +{result.expected_gain:.1f}."
        ),
        (
            f"Weekly gain formula: completed_minutes × effectiveness ({effectiveness_multiplier:.2f}) "
            f"× readiness_factor ({result.readiness_factor:.3f}) = {result.weekly_gain:.2f}."
        ),
        (
            f"Success probability {result.probability_of_success:.1f}% uses target gap, "
            f"adherence ({adherence_rate:.0%}), effectiveness history, and forecast stability."
        ),
        f"Target readiness is {target_readiness:.1f}; status is {result.forecast_status.replace('_', ' ')}.",
    ]
    if top_drivers:
        lines.append(f"Top drivers: {', '.join(top_drivers)}.")
    return lines
