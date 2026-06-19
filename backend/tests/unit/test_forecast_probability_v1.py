from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.forecast_explanations_v1 import explain_forecast_probability_v1
from prepos.domain.scoring.forecast_probability_v1 import (
    ForecastProbabilityInputs,
    ForecastScenario,
    ForecastScenarioInputs,
    GoalLikelihood,
    classify_goal_likelihood,
    compute_forecast_scenario,
    compute_forecast_scenarios_v1,
    compute_goal_probability_v1,
    compute_predicted_score_distribution,
)


def test_goal_probability_formula() -> None:
    probability = compute_goal_probability_v1(
        ForecastProbabilityInputs(
            current_readiness=Decimal("71.5"),
            projected_readiness=Decimal("81.2"),
            confidence_subscore=Decimal("70"),
            days_remaining=25,
        )
    )
    assert probability == Decimal("72.50")


def test_goal_probability_clamps_and_handles_missing_confidence() -> None:
    probability = compute_goal_probability_v1(
        ForecastProbabilityInputs(
            current_readiness=Decimal("95"),
            projected_readiness=Decimal("98"),
            confidence_subscore=None,
            days_remaining=120,
        )
    )
    assert probability == Decimal("68.80")


def test_goal_likelihood_classification() -> None:
    assert classify_goal_likelihood(Decimal("80")) == GoalLikelihood.VERY_LIKELY
    assert classify_goal_likelihood(Decimal("79.99")) == GoalLikelihood.LIKELY
    assert classify_goal_likelihood(Decimal("60")) == GoalLikelihood.LIKELY
    assert classify_goal_likelihood(Decimal("59.99")) == GoalLikelihood.UNCERTAIN
    assert classify_goal_likelihood(Decimal("40")) == GoalLikelihood.UNCERTAIN
    assert classify_goal_likelihood(Decimal("39.99")) == GoalLikelihood.UNLIKELY


def test_forecast_scenarios() -> None:
    inputs = ForecastScenarioInputs(
        projected_readiness=Decimal("81.2"),
        total_estimated_gain=Decimal("4.8"),
        retention_subscore=Decimal("55"),
    )
    result = compute_forecast_scenarios_v1(inputs)
    assert result.expected == Decimal("81.20")
    assert result.best_case == Decimal("86.00")
    assert result.worst_case == Decimal("74.45")

    assert compute_forecast_scenario(ForecastScenario.WORST_CASE, inputs=inputs) == Decimal("74.45")


def test_score_distribution_uses_uncertainty() -> None:
    distribution = compute_predicted_score_distribution(
        expected_score=Decimal("76.0"),
        confidence_subscore=Decimal("70"),
    )
    assert distribution.expected_score == Decimal("76.00")
    assert distribution.optimistic_score == Decimal("82.00")
    assert distribution.pessimistic_score == Decimal("70.00")


def test_forecast_probability_explanations_are_deterministic() -> None:
    probability_text = explain_forecast_probability_v1(
        goal_probability=Decimal("72.5"),
        confidence_subscore=Decimal("80"),
        total_estimated_gain=Decimal("0"),
    )
    assert probability_text == "You currently have a 72.5% likelihood of reaching your goal."

    low_confidence = explain_forecast_probability_v1(
        goal_probability=Decimal("72.5"),
        confidence_subscore=Decimal("65"),
        total_estimated_gain=Decimal("8"),
    )
    assert low_confidence == "Low confidence increases forecast uncertainty."

    gain = explain_forecast_probability_v1(
        goal_probability=Decimal("72.5"),
        confidence_subscore=Decimal("80"),
        total_estimated_gain=Decimal("8"),
    )
    assert gain == "Completing all planned revisions could improve readiness by 8 points."
