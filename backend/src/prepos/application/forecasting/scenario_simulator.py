from __future__ import annotations

from dataclasses import dataclass

from prepos.application.forecasting.goal_forecasting_engine import (
    ForecastEngineInputs,
    compute_probability_of_success,
    project_score_from_readiness,
    run_goal_forecast,
)

SCENARIO_BASELINE = "baseline"
SCENARIO_CURRENT_PLAN = "current_plan"
SCENARIO_STRETCH = "stretch_plan"
SCENARIO_REDUCED = "reduced_effort"
SCENARIO_CUSTOM = "custom_hours"
SCENARIO_AGGRESSIVE = "aggressive_plan"

DEFAULT_SCENARIO_MULTIPLIERS: dict[str, tuple[str, float]] = {
    SCENARIO_BASELINE: ("Baseline", 1.0),
    SCENARIO_CURRENT_PLAN: ("Current plan", 1.0),
    SCENARIO_STRETCH: ("Stretch plan", 1.67),
    SCENARIO_REDUCED: ("Reduced effort", 0.7),
    SCENARIO_AGGRESSIVE: ("Aggressive plan", 2.5),
}


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    scenario_type: str
    scenario_name: str
    weekly_minutes: int
    projected_readiness: float
    projected_score: float
    probability_of_success: float


def simulate_default_scenarios(
    *,
    base_weekly_minutes: int,
    engine_inputs: ForecastEngineInputs,
) -> list[ScenarioResult]:
    scenarios: list[ScenarioResult] = []
    seen_minutes: set[int] = set()
    for scenario_type, (name, multiplier) in DEFAULT_SCENARIO_MULTIPLIERS.items():
        weekly_minutes = max(60, int(round(base_weekly_minutes * multiplier)))
        if scenario_type == SCENARIO_CURRENT_PLAN and SCENARIO_BASELINE in {
            item.scenario_type for item in scenarios
        }:
            weekly_minutes = max(60, base_weekly_minutes)
        if weekly_minutes in seen_minutes and scenario_type != SCENARIO_CUSTOM:
            continue
        seen_minutes.add(weekly_minutes)
        result = run_goal_forecast(
            ForecastEngineInputs(
                current_readiness=engine_inputs.current_readiness,
                target_readiness=engine_inputs.target_readiness,
                weekly_minutes=float(weekly_minutes),
                adherence_rate=engine_inputs.adherence_rate,
                effectiveness_multiplier=engine_inputs.effectiveness_multiplier,
                forecast_stability=engine_inputs.forecast_stability,
                weeks_remaining=engine_inputs.weeks_remaining,
            )
        )
        scenarios.append(
            ScenarioResult(
                scenario_type=scenario_type,
                scenario_name=name,
                weekly_minutes=weekly_minutes,
                projected_readiness=result.projected_readiness,
                projected_score=project_score_from_readiness(result.projected_readiness),
                probability_of_success=result.probability_of_success,
            )
        )
    return sorted(scenarios, key=lambda item: item.weekly_minutes)


def simulate_custom_scenario(
    *,
    weekly_minutes: int,
    engine_inputs: ForecastEngineInputs,
) -> ScenarioResult:
    result = run_goal_forecast(
        ForecastEngineInputs(
            current_readiness=engine_inputs.current_readiness,
            target_readiness=engine_inputs.target_readiness,
            weekly_minutes=float(weekly_minutes),
            adherence_rate=engine_inputs.adherence_rate,
            effectiveness_multiplier=engine_inputs.effectiveness_multiplier,
            forecast_stability=engine_inputs.forecast_stability,
            weeks_remaining=engine_inputs.weeks_remaining,
        )
    )
    return ScenarioResult(
        scenario_type=SCENARIO_CUSTOM,
        scenario_name=f"Custom {weekly_minutes // 60}h/week",
        weekly_minutes=weekly_minutes,
        projected_readiness=result.projected_readiness,
        projected_score=project_score_from_readiness(result.projected_readiness),
        probability_of_success=result.probability_of_success,
    )
