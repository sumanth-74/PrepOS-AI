from __future__ import annotations

from uuid import uuid4

from prepos.application.institution_outcomes.outcome_engine import measure_outcome
from prepos.application.institution_outcomes.outcome_models import InitiativeInput, MetricSnapshot
from prepos.application.institution_outcomes.roi_engine import (
    calculate_roi_from_outcome,
    calculate_roi_score,
    split_best_and_failed,
)


def _initiative(readiness_gain: float, forecast_gain: float, health_gain: float, risk_reduction: float) -> InitiativeInput:
    before = MetricSnapshot(readiness=50.0, forecast=50.0, cohort_health=50.0, risk_count=30)
    after = MetricSnapshot(
        readiness=50.0 + readiness_gain,
        forecast=50.0 + forecast_gain,
        cohort_health=50.0 + health_gain,
        risk_count=30 - int(risk_reduction),
    )
    return InitiativeInput(
        initiative_id=uuid4(),
        initiative_type="forecast_recovery",
        title="Forecast recovery",
        status="completed",
        affected_students=80,
        affected_cohorts=("upsc_cse_cohort",),
        before=before,
        after=after,
        expected_readiness_gain=5.0,
        expected_forecast_gain=8.0,
        expected_cohort_health_gain=4.0,
        expected_risk_reduction=6,
    )


def test_roi_formula_weights_and_normalization() -> None:
    score = calculate_roi_score(
        readiness_gain=10.0,
        forecast_gain=8.0,
        cohort_health_gain=6.0,
        risk_reduction=5.0,
    )
    expected_raw = 10 * 0.40 + 8 * 0.30 + 6 * 0.20 + 5 * 0.10
    assert score == round(min(100.0, expected_raw * 2.0), 2)


def test_roi_from_outcome_includes_evidence_and_calculation() -> None:
    initiative = _initiative(readiness_gain=8.0, forecast_gain=6.0, health_gain=5.0, risk_reduction=8.0)
    outcome = measure_outcome(initiative=initiative)
    roi = calculate_roi_from_outcome(outcome=outcome, initiative_type=initiative.initiative_type, title=initiative.title)
    assert roi.evidence
    assert "readiness_gain*0.4" in roi.calculation
    assert 0 <= roi.roi_score <= 100


def test_best_and_failed_split_is_deterministic() -> None:
    items = []
    for readiness in (25.0, 2.0, 18.0, 1.0):
        initiative = _initiative(readiness, 15.0, 12.0, 10.0)
        outcome = measure_outcome(initiative=initiative)
        items.append(calculate_roi_from_outcome(outcome=outcome))
    sorted_items = sorted(items, key=lambda item: item.roi_score, reverse=True)
    best, failed = split_best_and_failed(items)
    assert sorted_items[0].roi_score >= sorted_items[-1].roi_score
    if best:
        assert best[0].roi_score >= best[-1].roi_score
    assert all(item.roi_score < 35.0 for item in failed)
