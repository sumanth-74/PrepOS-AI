from __future__ import annotations

from dataclasses import dataclass

MENTOR_INTERVENTION_V1 = "mentor_intervention_v1"

FORECAST_RISK_WEIGHT = 0.30
WEAKNESS_WEIGHT = 0.25
HISTORICAL_FAILURE_WEIGHT = 0.20
PYQ_IMPORTANCE_WEIGHT = 0.15
MEMORY_SIGNAL_WEIGHT = 0.10

ALLOWED_INTERVENTION_TYPES: frozenset[str] = frozenset(
    {
        "concept_revision",
        "extra_practice",
        "pyq_revision",
        "mentor_call",
        "coaching_session",
        "study_plan_adjustment",
        "current_affairs_revision",
        "goal_reset",
        "forecast_recovery_plan",
    }
)

BASE_GAIN_BY_TYPE: dict[str, float] = {
    "concept_revision": 3.2,
    "extra_practice": 2.6,
    "pyq_revision": 2.4,
    "mentor_call": 1.8,
    "coaching_session": 1.8,
    "study_plan_adjustment": 2.0,
    "current_affairs_revision": 2.2,
    "goal_reset": 1.5,
    "forecast_recovery_plan": 2.8,
}


@dataclass(frozen=True, slots=True)
class InterventionCandidateInput:
    intervention_type: str
    concept_id: str | None
    concept_name: str | None
    forecast_risk: float
    weakness: float
    historical_failure: float
    pyq_importance: float
    memory_signal: float


def normalize_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def compute_priority_score(inputs: InterventionCandidateInput) -> tuple[float, dict[str, float]]:
    forecast = normalize_score(inputs.forecast_risk)
    weakness = normalize_score(inputs.weakness)
    failure = normalize_score(inputs.historical_failure)
    pyq = normalize_score(inputs.pyq_importance)
    memory = normalize_score(inputs.memory_signal)
    priority = (
        forecast * FORECAST_RISK_WEIGHT
        + weakness * WEAKNESS_WEIGHT
        + failure * HISTORICAL_FAILURE_WEIGHT
        + pyq * PYQ_IMPORTANCE_WEIGHT
        + memory * MEMORY_SIGNAL_WEIGHT
    )
    breakdown = {
        "forecast_risk": forecast,
        "weakness": weakness,
        "historical_failure": failure,
        "pyq_importance": pyq,
        "memory_signal": memory,
        "priority_score": round(priority, 2),
    }
    return round(priority, 2), breakdown


def compute_predicted_gain(inputs: InterventionCandidateInput) -> float:
    base = BASE_GAIN_BY_TYPE.get(inputs.intervention_type, 2.0)
    weakness_factor = 0.5 + (normalize_score(inputs.weakness) / 100.0) * 0.5
    pyq_factor = 0.6 + (normalize_score(inputs.pyq_importance) / 100.0) * 0.4
    risk_factor = 0.5 + (normalize_score(inputs.forecast_risk) / 100.0) * 0.5

    if inputs.intervention_type in {"concept_revision", "extra_practice"}:
        multiplier = weakness_factor
    elif inputs.intervention_type == "pyq_revision":
        multiplier = pyq_factor
    elif inputs.intervention_type in {"forecast_recovery_plan", "study_plan_adjustment", "goal_reset"}:
        multiplier = risk_factor
    elif inputs.intervention_type == "current_affairs_revision":
        multiplier = (weakness_factor + pyq_factor) / 2.0
    else:
        multiplier = (weakness_factor + risk_factor) / 2.0

    return round(min(8.0, max(0.5, base * multiplier)), 2)


def compute_forecast_improvement(*, predicted_gain: float, forecast_risk: float) -> float:
    risk = normalize_score(forecast_risk) / 100.0
    return round(predicted_gain * (0.4 + risk * 0.6), 2)


def compute_confidence(inputs: InterventionCandidateInput, priority_score: float) -> str:
    if priority_score >= 80:
        return "high"
    if priority_score >= 55:
        return "medium"
    if inputs.memory_signal >= 60:
        return "medium"
    return "low"
