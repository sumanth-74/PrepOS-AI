from __future__ import annotations

from prepos.application.forecasting.goal_forecasting_engine import ForecastEngineInputs, run_goal_forecast
from prepos.application.forecasting.scenario_simulator import simulate_custom_scenario, simulate_default_scenarios


def test_golden_forecasting_for_one_hundred_students() -> None:
    for index in range(100):
        inputs = ForecastEngineInputs(
            current_readiness=40.0 + index * 0.3,
            target_readiness=70.0 + (index % 10),
            weekly_minutes=300.0 + (index % 5) * 60,
            adherence_rate=0.5 + (index % 5) * 0.1,
            effectiveness_multiplier=0.8 + (index % 4) * 0.2,
            forecast_stability=0.7 + (index % 3) * 0.1,
            weeks_remaining=4 + (index % 8),
        )
        first = run_goal_forecast(inputs)
        second = run_goal_forecast(inputs)
        assert first == second
        scenarios_a = simulate_default_scenarios(base_weekly_minutes=int(inputs.weekly_minutes), engine_inputs=inputs)
        scenarios_b = simulate_default_scenarios(base_weekly_minutes=int(inputs.weekly_minutes), engine_inputs=inputs)
        assert scenarios_a == scenarios_b
        custom = simulate_custom_scenario(weekly_minutes=600, engine_inputs=inputs)
        assert custom.projected_readiness >= first.projected_readiness or inputs.target_readiness <= first.projected_readiness
