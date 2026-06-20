from __future__ import annotations

from uuid import uuid4

from prepos.application.institution_outcomes.initiative_effectiveness import evaluate_all_initiatives
from prepos.application.institution_outcomes.outcome_engine import measure_outcomes
from prepos.application.institution_outcomes.outcome_models import InitiativeInput, MetricSnapshot
from prepos.application.institution_outcomes.roi_engine import calculate_roi_for_initiatives


def _synthetic_institution(index: int) -> list[InitiativeInput]:
    initiatives: list[InitiativeInput] = []
    initiative_count = 1 + (index % 3)
    for offset in range(initiative_count):
        readiness_gain = 2.0 + ((index + offset) % 10)
        forecast_gain = 1.0 + ((index + offset) % 8)
        health_gain = 1.5 + ((index + offset) % 7)
        risk_reduction = (index + offset) % 6
        before = MetricSnapshot(
            readiness=45.0 + (index % 15),
            forecast=44.0 + (index % 12),
            cohort_health=46.0 + (index % 10),
            risk_count=20 + (index % 10),
        )
        after = MetricSnapshot(
            readiness=before.readiness + readiness_gain,
            forecast=before.forecast + forecast_gain,
            cohort_health=before.cohort_health + health_gain,
            risk_count=max(0, before.risk_count - risk_reduction),
        )
        initiatives.append(
            InitiativeInput(
                initiative_id=uuid4(),
                initiative_type=[
                    "revision_campaign",
                    "mentor_training",
                    "current_affairs_boost",
                    "forecast_recovery",
                    "weak_concept_program",
                    "pyq_focus_program",
                ][(index + offset) % 6],
                title=f"Initiative {index}-{offset}",
                status="completed",
                affected_students=80 + offset * 10,
                affected_cohorts=(f"cohort_{index % 5}",),
                before=before,
                after=after,
                expected_readiness_gain=5.0,
                expected_forecast_gain=4.0,
                expected_cohort_health_gain=4.0,
                expected_risk_reduction=5,
            )
        )
    return initiatives


def test_golden_institution_outcome_roi_for_one_hundred_institutions() -> None:
    for index in range(100):
        initiatives = _synthetic_institution(index)
        outcomes = measure_outcomes(initiatives)
        first_roi = calculate_roi_for_initiatives(initiatives=initiatives, outcomes=outcomes)
        second_roi = calculate_roi_for_initiatives(initiatives=initiatives, outcomes=outcomes)
        assert first_roi == second_roi
        if len(first_roi) >= 2:
            assert first_roi[0].roi_score >= first_roi[-1].roi_score

        first_effectiveness = evaluate_all_initiatives(initiatives=initiatives, outcomes=outcomes)
        second_effectiveness = evaluate_all_initiatives(initiatives=initiatives, outcomes=outcomes)
        assert first_effectiveness == second_effectiveness
