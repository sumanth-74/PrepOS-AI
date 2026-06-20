from __future__ import annotations


def compute_actual_gain(*, readiness_before: float, readiness_after: float) -> float:
    return round(max(-10.0, min(10.0, readiness_after - readiness_before)), 2)


def compute_effectiveness_score(*, predicted_gain: float, actual_gain: float) -> float:
    if predicted_gain <= 0:
        return 0.0 if actual_gain <= 0 else 100.0
    ratio = actual_gain / predicted_gain
    score = ratio * 100.0
    return round(max(0.0, min(150.0, score)), 2)


def classify_intervention_outcome(effectiveness_score: float) -> str:
    if effectiveness_score >= 80:
        return "intervention_success"
    if effectiveness_score >= 40:
        return "intervention_completed"
    return "intervention_failure"
