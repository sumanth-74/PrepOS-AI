from __future__ import annotations

COHORT_SEGMENTATION_V1 = "cohort_segmentation_v1"

SEGMENT_PRIORITY: tuple[str, ...] = (
    "critical_risk",
    "at_risk",
    "intervention_resistant",
    "stagnant",
    "recovering",
    "high_performer",
    "high_potential",
    "intervention_responder",
    "on_track",
)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return round(max(low, min(high, value)), 2)


def compute_risk_score(inputs: "StudentCohortInput") -> tuple[float, tuple[str, ...]]:
    from prepos.application.cohort.cohort_models import StudentCohortInput

    assert isinstance(inputs, StudentCohortInput)
    factors: list[str] = []
    readiness_penalty = max(0.0, 70.0 - inputs.readiness) * 0.6
    if inputs.readiness < 55:
        factors.append("low readiness")
    forecast_penalty = max(0.0, 75.0 - inputs.forecast_probability) * 0.5
    if inputs.forecast_probability < 60:
        factors.append("low forecast probability")
    adherence_penalty = max(0.0, 60.0 - inputs.planning_adherence) * 0.3
    if inputs.planning_adherence < 50:
        factors.append("poor plan adherence")
    intervention_penalty = 0.0
    if inputs.failed_intervention_count > 0:
        intervention_penalty = min(25.0, inputs.failed_intervention_count * 8.0)
        factors.append("failed interventions")
    if not inputs.on_track:
        factors.append("off track forecast")
        readiness_penalty += 8.0
    if inputs.readiness_delta < -1.0:
        factors.append("slipping readiness")
        readiness_penalty += 10.0

    raw = readiness_penalty + forecast_penalty + adherence_penalty + intervention_penalty
    return _clamp(raw), tuple(factors)


def classify_segment(inputs: "StudentCohortInput") -> tuple[str, float]:
    from prepos.application.cohort.cohort_models import StudentCohortInput

    assert isinstance(inputs, StudentCohortInput)
    matches: dict[str, float] = {}

    if inputs.readiness < 40 and inputs.forecast_probability < 50:
        matches["critical_risk"] = 95.0
    if inputs.readiness < 55 or inputs.forecast_probability < 60 or not inputs.on_track:
        matches["at_risk"] = max(70.0, 100.0 - inputs.readiness)
    if inputs.intervention_count >= 2 and inputs.intervention_effectiveness < 40:
        matches["intervention_resistant"] = 80.0
    if inputs.weekly_progress < 1.0 and inputs.consistency_score < 45:
        matches["stagnant"] = 65.0
    if inputs.readiness_delta >= 2.0 and inputs.readiness < 75:
        matches["recovering"] = 60.0 + inputs.readiness_delta
    if inputs.readiness >= 80 and inputs.forecast_probability >= 85:
        matches["high_performer"] = inputs.readiness
    if 55 <= inputs.readiness < 75 and inputs.recommendation_effectiveness >= 60:
        matches["high_potential"] = 55.0 + inputs.recommendation_effectiveness * 0.3
    if inputs.intervention_count >= 1 and inputs.intervention_effectiveness >= 80:
        matches["intervention_responder"] = inputs.intervention_effectiveness
    matches["on_track"] = max(40.0, min(inputs.readiness, inputs.forecast_probability))

    for segment in SEGMENT_PRIORITY:
        if segment in matches:
            return segment, _clamp(matches[segment])
    return "on_track", 50.0


def segment_student(inputs: "StudentCohortInput") -> "SegmentationResult":
    from prepos.application.cohort.cohort_models import SegmentationResult, StudentCohortInput

    assert isinstance(inputs, StudentCohortInput)
    segment_type, segment_score = classify_segment(inputs)
    risk_score, risk_factors = compute_risk_score(inputs)
    return SegmentationResult(
        segment_type=segment_type,
        segment_score=segment_score,
        risk_score=risk_score,
        risk_factors=risk_factors,
    )
