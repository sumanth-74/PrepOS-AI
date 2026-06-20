from __future__ import annotations

from prepos.application.interventions.intervention_engine import (
    ALLOWED_INTERVENTION_TYPES,
    InterventionCandidateInput,
    compute_confidence,
    compute_forecast_improvement,
    compute_predicted_gain,
    compute_priority_score,
)
from prepos.application.interventions.intervention_models import InterventionScoreBreakdown, RankedIntervention
from prepos.application.recommendations.recommendation_engine import format_concept_name


def build_intervention_reason(
    *,
    intervention_type: str,
    concept_name: str | None,
    weakness: float,
    pyq_importance: float,
    forecast_risk: float,
    historical_failure: float,
) -> str:
    parts: list[str] = []
    if weakness >= 60:
        parts.append("high weakness")
    if pyq_importance >= 60:
        parts.append("high PYQ frequency")
    if forecast_risk >= 60:
        parts.append("forecast risk")
    if historical_failure >= 50:
        parts.append("historical underperformance")
    if not parts:
        parts.append("balanced readiness opportunity")
    label = concept_name or intervention_type.replace("_", " ")
    return f"{label}: {' + '.join(parts)}"


def rank_intervention_candidate(inputs: InterventionCandidateInput) -> RankedIntervention:
    priority_score, breakdown = compute_priority_score(inputs)
    predicted_gain = compute_predicted_gain(inputs)
    return RankedIntervention(
        intervention_type=inputs.intervention_type,
        concept_id=inputs.concept_id,
        concept_name=inputs.concept_name,
        reason=build_intervention_reason(
            intervention_type=inputs.intervention_type,
            concept_name=inputs.concept_name,
            weakness=inputs.weakness,
            pyq_importance=inputs.pyq_importance,
            forecast_risk=inputs.forecast_risk,
            historical_failure=inputs.historical_failure,
        ),
        predicted_gain=predicted_gain,
        priority_score=priority_score,
        impact_score=priority_score,
        confidence=compute_confidence(inputs, priority_score),
        forecast_improvement=compute_forecast_improvement(
            predicted_gain=predicted_gain,
            forecast_risk=inputs.forecast_risk,
        ),
        score_breakdown=InterventionScoreBreakdown(**breakdown),
    )


def optimize_interventions(
    *,
    concept_candidates: list[dict[str, float | str]],
    forecast_risk: float,
    memory_signal: float,
    limit: int = 5,
) -> list[RankedIntervention]:
    ranked: list[RankedIntervention] = []

    for index, raw in enumerate(concept_candidates[:8]):
        concept_id = str(raw.get("concept_id", ""))
        concept_name = str(raw.get("concept_name", format_concept_name(concept_id)))
        weakness = float(raw.get("weakness", 50.0))
        pyq = float(raw.get("pyq_importance", 40.0))
        failure = float(raw.get("historical_failure", 30.0))
        risk = float(raw.get("forecast_risk", forecast_risk))

        type_sequence = [
            "concept_revision",
            "pyq_revision",
            "extra_practice",
            "current_affairs_revision",
        ]
        intervention_type = type_sequence[index % len(type_sequence)]
        if index == 0 and forecast_risk >= 65:
            intervention_type = "forecast_recovery_plan"
        elif index == 1 and weakness >= 70:
            intervention_type = "concept_revision"

        candidate = InterventionCandidateInput(
            intervention_type=intervention_type,
            concept_id=concept_id or None,
            concept_name=concept_name,
            forecast_risk=risk,
            weakness=weakness,
            historical_failure=failure,
            pyq_importance=pyq,
            memory_signal=memory_signal,
        )
        if intervention_type in ALLOWED_INTERVENTION_TYPES:
            ranked.append(rank_intervention_candidate(candidate))

    global_types = [
        ("study_plan_adjustment", None, "Study plan", forecast_risk, 45.0, 35.0, 30.0),
        ("mentor_call", None, "Mentor call", forecast_risk, 55.0, 25.0, memory_signal),
        ("coaching_session", None, "Coaching", max(forecast_risk, memory_signal), 50.0, 20.0, memory_signal),
    ]
    if forecast_risk >= 70:
        global_types.insert(0, ("goal_reset", None, "Goal reset", forecast_risk, 40.0, 45.0, 35.0))

    for intervention_type, concept_id, concept_name, risk, weakness, failure, pyq in global_types:
        candidate = InterventionCandidateInput(
            intervention_type=intervention_type,
            concept_id=concept_id,
            concept_name=concept_name,
            forecast_risk=risk,
            weakness=weakness,
            historical_failure=failure,
            pyq_importance=pyq,
            memory_signal=memory_signal,
        )
        ranked.append(rank_intervention_candidate(candidate))

    ranked.sort(key=lambda item: (item.priority_score, item.predicted_gain), reverse=True)
    deduped: list[RankedIntervention] = []
    seen: set[tuple[str, str | None]] = set()
    for item in ranked:
        key = (item.intervention_type, item.concept_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped
