from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from prepos.domain.scoring.common import clamp, round_score
from prepos.domain.scoring.exam_simulation_v1 import compute_retention_decay_penalty
from prepos.domain.scoring.predicted_score_v1 import compute_score_uncertainty

FORECAST_PROBABILITY_V1 = "forecast_probability_v1"

_W_READINESS = Decimal("0.60")
_W_CONFIDENCE = Decimal("0.30")
_W_TIME = Decimal("0.10")
_TIME_HORIZON_DAYS = Decimal("90")


class ForecastScenario(StrEnum):
    BEST_CASE = "BEST_CASE"
    EXPECTED = "EXPECTED"
    WORST_CASE = "WORST_CASE"


class GoalLikelihood(StrEnum):
    VERY_LIKELY = "VERY_LIKELY"
    LIKELY = "LIKELY"
    UNCERTAIN = "UNCERTAIN"
    UNLIKELY = "UNLIKELY"


@dataclass(frozen=True, slots=True)
class ForecastProbabilityInputs:
    current_readiness: Decimal
    projected_readiness: Decimal
    confidence_subscore: Decimal | None
    days_remaining: int


@dataclass(frozen=True, slots=True)
class ForecastScenarioInputs:
    projected_readiness: Decimal
    total_estimated_gain: Decimal
    retention_subscore: Decimal | None


@dataclass(frozen=True, slots=True)
class ForecastScenarioResult:
    best_case: Decimal
    expected: Decimal
    worst_case: Decimal


@dataclass(frozen=True, slots=True)
class PredictedScoreDistribution:
    expected_score: Decimal
    optimistic_score: Decimal
    pessimistic_score: Decimal


def compute_goal_probability_v1(inputs: ForecastProbabilityInputs) -> Decimal:
    readiness_factor = inputs.projected_readiness / Decimal("100")
    confidence = inputs.confidence_subscore if inputs.confidence_subscore is not None else Decimal("0")
    confidence_factor = confidence / Decimal("100")
    time_factor = min(Decimal(inputs.days_remaining) / _TIME_HORIZON_DAYS, Decimal("1"))
    raw = (
        readiness_factor * _W_READINESS
        + confidence_factor * _W_CONFIDENCE
        + time_factor * _W_TIME
    ) * Decimal("100")
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))


def classify_goal_likelihood(goal_probability: Decimal) -> GoalLikelihood:
    if goal_probability >= Decimal("80"):
        return GoalLikelihood.VERY_LIKELY
    if goal_probability >= Decimal("60"):
        return GoalLikelihood.LIKELY
    if goal_probability >= Decimal("40"):
        return GoalLikelihood.UNCERTAIN
    return GoalLikelihood.UNLIKELY


def _clamp_readiness(value: Decimal) -> Decimal:
    return round_score(clamp(value, Decimal("0"), Decimal("100")))


def compute_forecast_scenario(
    scenario: ForecastScenario,
    *,
    inputs: ForecastScenarioInputs,
) -> Decimal:
    if scenario == ForecastScenario.EXPECTED:
        return _clamp_readiness(inputs.projected_readiness)
    if scenario == ForecastScenario.BEST_CASE:
        return _clamp_readiness(inputs.projected_readiness + inputs.total_estimated_gain)
    penalty = compute_retention_decay_penalty(inputs.retention_subscore)
    return _clamp_readiness(inputs.projected_readiness - penalty)


def compute_forecast_scenarios_v1(inputs: ForecastScenarioInputs) -> ForecastScenarioResult:
    return ForecastScenarioResult(
        best_case=compute_forecast_scenario(ForecastScenario.BEST_CASE, inputs=inputs),
        expected=compute_forecast_scenario(ForecastScenario.EXPECTED, inputs=inputs),
        worst_case=compute_forecast_scenario(ForecastScenario.WORST_CASE, inputs=inputs),
    )


def compute_predicted_score_distribution(
    *,
    expected_score: Decimal,
    confidence_subscore: Decimal | None,
) -> PredictedScoreDistribution:
    uncertainty = round_score(compute_score_uncertainty(confidence_subscore))
    optimistic = round_score(clamp(expected_score + uncertainty, Decimal("0"), Decimal("100")))
    pessimistic = round_score(clamp(expected_score - uncertainty, Decimal("0"), Decimal("100")))
    return PredictedScoreDistribution(
        expected_score=expected_score,
        optimistic_score=optimistic,
        pessimistic_score=pessimistic,
    )
