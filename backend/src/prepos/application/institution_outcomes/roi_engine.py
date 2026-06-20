from __future__ import annotations

from prepos.application.institution_outcomes.outcome_models import InitiativeInput, OutcomeItem, RoiEvidence, RoiItem

ROI_ENGINE_V1 = "roi_engine_v1"

READINESS_WEIGHT = 0.40
FORECAST_WEIGHT = 0.30
COHORT_HEALTH_WEIGHT = 0.20
RISK_REDUCTION_WEIGHT = 0.10

ROI_SUCCESS_THRESHOLD = 60.0
ROI_FAILED_THRESHOLD = 35.0


def calculate_roi_score(
    *,
    readiness_gain: float,
    forecast_gain: float,
    cohort_health_gain: float,
    risk_reduction: float,
) -> float:
    raw = (
        max(0.0, readiness_gain) * READINESS_WEIGHT
        + max(0.0, forecast_gain) * FORECAST_WEIGHT
        + max(0.0, cohort_health_gain) * COHORT_HEALTH_WEIGHT
        + max(0.0, risk_reduction) * RISK_REDUCTION_WEIGHT
    )
    return round(min(100.0, raw * 2.0), 2)


def calculate_roi_from_outcome(
    *,
    outcome: OutcomeItem,
    initiative_type: str | None = None,
    title: str | None = None,
) -> RoiItem:
    roi_score = calculate_roi_score(
        readiness_gain=outcome.readiness_gain,
        forecast_gain=outcome.forecast_gain,
        cohort_health_gain=outcome.cohort_health_gain,
        risk_reduction=outcome.risk_reduction,
    )
    calculation = (
        f"roi_score = min(100, 2 * (readiness_gain*{READINESS_WEIGHT} + "
        f"forecast_gain*{FORECAST_WEIGHT} + cohort_health_gain*{COHORT_HEALTH_WEIGHT} + "
        f"risk_reduction*{RISK_REDUCTION_WEIGHT}))"
    )
    return RoiItem(
        initiative_id=outcome.initiative_id,
        subject_key=outcome.subject_key,
        initiative_type=initiative_type,
        title=title,
        roi_score=roi_score,
        readiness_gain=outcome.readiness_gain,
        forecast_gain=outcome.forecast_gain,
        cohort_health_gain=outcome.cohort_health_gain,
        risk_reduction=outcome.risk_reduction,
        evidence=[
            RoiEvidence(label="Readiness gain", value=f"{outcome.readiness_gain:+.2f}"),
            RoiEvidence(label="Forecast gain", value=f"{outcome.forecast_gain:+.2f}"),
            RoiEvidence(label="Cohort health gain", value=f"{outcome.cohort_health_gain:+.2f}"),
            RoiEvidence(label="Risk reduction", value=f"{outcome.risk_reduction:+.0f}"),
            RoiEvidence(label="Variance vs expected", value=f"{outcome.variance:+.2f}"),
        ],
        calculation=calculation,
    )


def calculate_roi_for_initiatives(
    *,
    initiatives: list[InitiativeInput],
    outcomes: list[OutcomeItem],
) -> list[RoiItem]:
    outcome_map = {outcome.initiative_id: outcome for outcome in outcomes if outcome.initiative_id}
    items: list[RoiItem] = []
    for initiative in initiatives:
        outcome = outcome_map.get(initiative.initiative_id)
        if outcome is None:
            continue
        items.append(
            calculate_roi_from_outcome(
                outcome=outcome,
                initiative_type=initiative.initiative_type,
                title=initiative.title,
            )
        )
    return sorted(items, key=lambda item: item.roi_score, reverse=True)


def split_best_and_failed(items: list[RoiItem]) -> tuple[list[RoiItem], list[RoiItem]]:
    best = [item for item in items if item.roi_score >= ROI_SUCCESS_THRESHOLD]
    failed = [item for item in items if item.roi_score < ROI_FAILED_THRESHOLD]
    return best, failed
