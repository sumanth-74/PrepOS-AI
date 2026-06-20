from __future__ import annotations

from dataclasses import dataclass

GOAL_FORECASTING_V1 = "goal_forecasting_v1"

READINESS_FACTOR_MIN = 0.015
READINESS_FACTOR_MAX = 0.045
WEEKLY_GAIN_CAP = 12.0

GAP_WEIGHT = 0.40
ADHERENCE_WEIGHT = 0.25
EFFECTIVENESS_WEIGHT = 0.20
STABILITY_WEIGHT = 0.15


@dataclass(frozen=True, slots=True)
class ForecastEngineInputs:
    current_readiness: float
    target_readiness: float
    weekly_minutes: float
    adherence_rate: float
    effectiveness_multiplier: float
    forecast_stability: float
    weeks_remaining: int


@dataclass(frozen=True, slots=True)
class ForecastEngineResult:
    projected_readiness: float
    expected_gain: float
    weekly_gain: float
    probability_of_success: float
    forecast_status: str
    readiness_factor: float


def compute_readiness_factor(*, current_readiness: float) -> float:
    room_to_grow = max(0.0, 100.0 - current_readiness)
    factor = READINESS_FACTOR_MIN + (room_to_grow / 100.0) * (READINESS_FACTOR_MAX - READINESS_FACTOR_MIN)
    return round(factor, 4)


def compute_weekly_gain(
    *,
    completed_minutes: float,
    effectiveness_multiplier: float,
    readiness_factor: float,
) -> float:
    raw = completed_minutes * effectiveness_multiplier * readiness_factor
    return round(min(WEEKLY_GAIN_CAP, max(0.0, raw)), 2)


def compute_expected_gain(*, weekly_gain: float, weeks_remaining: int) -> float:
    return round(min(WEEKLY_GAIN_CAP * max(weeks_remaining, 1), weekly_gain * max(weeks_remaining, 1)), 2)


def compute_probability_of_success(
    *,
    projected_readiness: float,
    target_readiness: float,
    adherence_rate: float,
    effectiveness_multiplier: float,
    forecast_stability: float,
) -> float:
    gap = max(0.0, target_readiness - projected_readiness)
    gap_factor = max(0.0, 100.0 - gap * 2.5)
    adherence_factor = max(0.0, min(100.0, adherence_rate * 100.0))
    effectiveness_factor = max(0.0, min(100.0, effectiveness_multiplier * 33.33))
    stability_factor = max(0.0, min(100.0, forecast_stability * 100.0))
    raw = (
        gap_factor * GAP_WEIGHT
        + adherence_factor * ADHERENCE_WEIGHT
        + effectiveness_factor * EFFECTIVENESS_WEIGHT
        + stability_factor * STABILITY_WEIGHT
    )
    if projected_readiness >= target_readiness:
        raw = max(raw, 85.0)
    return round(min(100.0, max(0.0, raw)), 1)


def classify_forecast_status(
    *,
    projected_readiness: float,
    target_readiness: float,
    probability_of_success: float,
) -> str:
    if projected_readiness >= target_readiness:
        return "on_track"
    if probability_of_success >= 60.0:
        return "at_risk"
    return "off_track"


def run_goal_forecast(inputs: ForecastEngineInputs) -> ForecastEngineResult:
    readiness_factor = compute_readiness_factor(current_readiness=inputs.current_readiness)
    weekly_gain = compute_weekly_gain(
        completed_minutes=inputs.weekly_minutes,
        effectiveness_multiplier=inputs.effectiveness_multiplier,
        readiness_factor=readiness_factor,
    )
    expected_gain = compute_expected_gain(
        weekly_gain=weekly_gain,
        weeks_remaining=inputs.weeks_remaining,
    )
    projected = round(min(100.0, inputs.current_readiness + expected_gain), 1)
    probability = compute_probability_of_success(
        projected_readiness=projected,
        target_readiness=inputs.target_readiness,
        adherence_rate=inputs.adherence_rate,
        effectiveness_multiplier=inputs.effectiveness_multiplier,
        forecast_stability=inputs.forecast_stability,
    )
    status = classify_forecast_status(
        projected_readiness=projected,
        target_readiness=inputs.target_readiness,
        probability_of_success=probability,
    )
    return ForecastEngineResult(
        projected_readiness=projected,
        expected_gain=expected_gain,
        weekly_gain=weekly_gain,
        probability_of_success=probability,
        forecast_status=status,
        readiness_factor=readiness_factor,
    )


def project_score_from_readiness(readiness: float) -> float:
    return round(min(100.0, readiness * 0.95 + 5.0), 1)
