from __future__ import annotations

import pytest

from prepos.application.forecasting.goal_forecasting_engine import (
    ForecastEngineInputs,
    compute_probability_of_success,
    run_goal_forecast,
)
from prepos.application.forecasting.scenario_simulator import simulate_custom_scenario, simulate_default_scenarios


def test_weekly_gain_formula_is_deterministic() -> None:
    inputs = ForecastEngineInputs(
        current_readiness=62.0,
        target_readiness=75.0,
        weekly_minutes=360.0,
        adherence_rate=0.8,
        effectiveness_multiplier=1.2,
        forecast_stability=0.9,
        weeks_remaining=8,
    )
    first = run_goal_forecast(inputs)
    second = run_goal_forecast(inputs)
    assert first == second
    assert first.weekly_gain > 0


def test_probability_increases_with_better_adherence() -> None:
    low = compute_probability_of_success(
        projected_readiness=70.0,
        target_readiness=75.0,
        adherence_rate=0.3,
        effectiveness_multiplier=1.0,
        forecast_stability=0.8,
    )
    high = compute_probability_of_success(
        projected_readiness=70.0,
        target_readiness=75.0,
        adherence_rate=0.9,
        effectiveness_multiplier=1.0,
        forecast_stability=0.8,
    )
    assert high > low


def test_scenario_minutes_monotonicity() -> None:
    inputs = ForecastEngineInputs(
        current_readiness=60.0,
        target_readiness=75.0,
        weekly_minutes=360.0,
        adherence_rate=0.75,
        effectiveness_multiplier=1.0,
        forecast_stability=0.85,
        weeks_remaining=10,
    )
    scenarios = simulate_default_scenarios(base_weekly_minutes=360, engine_inputs=inputs)
    minutes = [item.weekly_minutes for item in scenarios]
    readiness = [item.projected_readiness for item in scenarios]
    assert minutes == sorted(minutes)
    assert readiness == sorted(readiness)
