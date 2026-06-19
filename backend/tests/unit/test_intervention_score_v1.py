from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.intervention_score_v1 import (
    compute_expected_impact_score,
    compute_intervention_score_v1,
    urgency_to_score,
)


def test_urgency_to_score_mapping() -> None:
    assert urgency_to_score("CRITICAL") == Decimal("100")
    assert urgency_to_score("HIGH") == Decimal("75")
    assert urgency_to_score("MEDIUM") == Decimal("50")
    assert urgency_to_score("LOW") == Decimal("25")


def test_expected_impact_scales_readiness_gain() -> None:
    assert compute_expected_impact_score(Decimal("3.2")) == Decimal("32.00")
    assert compute_expected_impact_score(Decimal("12.5")) == Decimal("100.00")


def test_intervention_score_formula() -> None:
    score = compute_intervention_score_v1(
        decision_score=Decimal("84.5"),
        urgency="HIGH",
        expected_readiness_gain=Decimal("3.2"),
    )
    assert score == Decimal("71.15")
