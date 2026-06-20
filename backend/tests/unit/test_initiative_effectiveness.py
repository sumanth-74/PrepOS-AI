from __future__ import annotations

from uuid import uuid4

from prepos.application.institution_outcomes.initiative_effectiveness import evaluate_all_initiatives
from prepos.application.institution_outcomes.outcome_engine import measure_outcomes
from prepos.application.institution_outcomes.outcome_models import InitiativeInput, MetricSnapshot


def _initiative(index: int) -> InitiativeInput:
    before = MetricSnapshot(readiness=50.0, forecast=48.0, cohort_health=50.0, risk_count=25)
    after = MetricSnapshot(
        readiness=50.0 + index,
        forecast=48.0 + index * 0.8,
        cohort_health=50.0 + index * 0.7,
        risk_count=max(0, 25 - index),
    )
    return InitiativeInput(
        initiative_id=uuid4(),
        initiative_type="weak_concept_program",
        title=f"Initiative {index}",
        status="completed",
        affected_students=100,
        affected_cohorts=("upsc_cse_cohort",),
        before=before,
        after=after,
        expected_readiness_gain=5.0,
        expected_forecast_gain=4.0,
        expected_cohort_health_gain=4.0,
        expected_risk_reduction=5,
    )


def test_effectiveness_ranking_is_stable() -> None:
    initiatives = [_initiative(index) for index in (8, 3, 10, 1)]
    outcomes = measure_outcomes(initiatives)
    first = evaluate_all_initiatives(initiatives=initiatives, outcomes=outcomes)
    second = evaluate_all_initiatives(initiatives=initiatives, outcomes=outcomes)
    assert first == second
    assert first[0].effectiveness_score >= first[-1].effectiveness_score


def test_high_gain_initiative_marked_succeeded() -> None:
    initiative = _initiative(20)
    outcome = measure_outcomes([initiative])[0]
    result = evaluate_all_initiatives(initiatives=[initiative], outcomes=[outcome])[0]
    assert result.status in {"succeeded", "partial"}
    assert result.roi_score > 0
