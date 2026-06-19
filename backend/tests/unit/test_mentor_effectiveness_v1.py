from __future__ import annotations

from decimal import Decimal

from prepos.domain.mentor.mentor_effectiveness_v1 import (
    CaseEffectivenessInputs,
    compute_mentor_effectiveness_v1,
)


def test_effectiveness_score_uses_weighted_formula() -> None:
    effectiveness = compute_mentor_effectiveness_v1(
        CaseEffectivenessInputs(
            total_cases=10,
            resolved_cases=8,
            risk_reduced_cases=4,
            successful_interventions=6,
            total_resolution_hours=Decimal("24"),
        )
    )
    resolution_rate = Decimal("80")
    risk_reduction_rate = Decimal("50")
    intervention_success_rate = Decimal("75")
    expected = (
        resolution_rate * Decimal("0.40")
        + risk_reduction_rate * Decimal("0.30")
        + intervention_success_rate * Decimal("0.30")
    )
    assert effectiveness.effectiveness_score == expected.quantize(Decimal("0.01"))
    assert effectiveness.cases_resolved == 8
    assert effectiveness.average_resolution_time_hours == Decimal("3.00")
    assert effectiveness.risk_reduction_rate == Decimal("50.00")


def test_effectiveness_score_clamped_when_no_cases() -> None:
    effectiveness = compute_mentor_effectiveness_v1(
        CaseEffectivenessInputs(
            total_cases=0,
            resolved_cases=0,
            risk_reduced_cases=0,
            successful_interventions=0,
            total_resolution_hours=Decimal("0"),
        )
    )
    assert effectiveness.effectiveness_score == Decimal("0.00")
