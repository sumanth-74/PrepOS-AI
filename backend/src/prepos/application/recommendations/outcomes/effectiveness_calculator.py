from __future__ import annotations

EFFECTIVENESS_SCORE_MAX = 3.0
SUCCESS_EFFECTIVENESS_THRESHOLD = 1.0
PARTIAL_EFFECTIVENESS_THRESHOLD = 0.5


def calculate_actual_gain(*, readiness_before: float, readiness_after: float) -> float:
    return round(readiness_after - readiness_before, 2)


def calculate_effectiveness_score(*, actual_gain: float, predicted_gain: float) -> float:
    if predicted_gain <= 0:
        return 0.0
    raw = actual_gain / predicted_gain
    return round(max(0.0, min(EFFECTIVENESS_SCORE_MAX, raw)), 2)


def calculate_forecast_delta(*, forecast_before: float, forecast_after: float) -> float:
    return round(forecast_after - forecast_before, 2)


def calculate_weakness_delta(*, weakness_before: float, weakness_after: float) -> float:
    return round(weakness_before - weakness_after, 2)


def outcome_status(*, effectiveness_score: float, actual_gain: float) -> str:
    if effectiveness_score >= SUCCESS_EFFECTIVENESS_THRESHOLD and actual_gain > 0:
        return "successful"
    if effectiveness_score >= PARTIAL_EFFECTIVENESS_THRESHOLD:
        return "partial"
    return "failed"


def build_score_breakdown(
    *,
    weakness_score: float,
    pyq_frequency_score: float,
    forecast_gain_score: float,
    current_affairs_score: float,
    weakness_weight: float = 0.40,
    pyq_weight: float = 0.30,
    forecast_weight: float = 0.20,
    current_affairs_weight: float = 0.10,
) -> dict[str, float]:
    return {
        "weakness": round(weakness_score * weakness_weight / 10.0, 1),
        "pyq": round(pyq_frequency_score * pyq_weight / 10.0, 1),
        "forecast": round(forecast_gain_score * forecast_weight / 10.0, 1),
        "current_affairs": round(current_affairs_score * current_affairs_weight / 10.0, 1),
    }
