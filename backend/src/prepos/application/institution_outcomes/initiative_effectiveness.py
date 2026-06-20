from __future__ import annotations

from prepos.application.institution_outcomes.outcome_models import (
    InitiativeEffectivenessItem,
    InitiativeInput,
    OutcomeItem,
)
from prepos.application.institution_outcomes.roi_engine import (
    ROI_FAILED_THRESHOLD,
    ROI_SUCCESS_THRESHOLD,
    calculate_roi_score,
)

INITIATIVE_EFFECTIVENESS_V1 = "initiative_effectiveness_v1"


def evaluate_initiative_effectiveness(
    *,
    initiative: InitiativeInput,
    outcome: OutcomeItem,
) -> InitiativeEffectivenessItem:
    roi_score = calculate_roi_score(
        readiness_gain=outcome.readiness_gain,
        forecast_gain=outcome.forecast_gain,
        cohort_health_gain=outcome.cohort_health_gain,
        risk_reduction=outcome.risk_reduction,
    )
    effectiveness_score = round(min(100.0, roi_score + max(0.0, -outcome.variance)), 2)
    status = _status_for_scores(roi_score=roi_score, variance=outcome.variance)
    return InitiativeEffectivenessItem(
        initiative_id=initiative.initiative_id,
        initiative_type=initiative.initiative_type,
        title=initiative.title,
        effectiveness_score=effectiveness_score,
        readiness_delta=outcome.readiness_gain,
        forecast_delta=outcome.forecast_gain,
        cohort_health_delta=outcome.cohort_health_gain,
        risk_reduction=int(outcome.risk_reduction),
        roi_score=roi_score,
        status=status,
    )


def evaluate_all_initiatives(
    *,
    initiatives: list[InitiativeInput],
    outcomes: list[OutcomeItem],
) -> list[InitiativeEffectivenessItem]:
    outcome_map = {outcome.initiative_id: outcome for outcome in outcomes if outcome.initiative_id}
    items: list[InitiativeEffectivenessItem] = []
    for initiative in initiatives:
        outcome = outcome_map.get(initiative.initiative_id)
        if outcome is None:
            continue
        items.append(evaluate_initiative_effectiveness(initiative=initiative, outcome=outcome))
    return sorted(items, key=lambda item: item.effectiveness_score, reverse=True)


def _status_for_scores(*, roi_score: float, variance: float) -> str:
    if roi_score >= ROI_SUCCESS_THRESHOLD and variance >= -2.0:
        return "succeeded"
    if roi_score < ROI_FAILED_THRESHOLD or variance <= -5.0:
        return "failed"
    return "partial"
