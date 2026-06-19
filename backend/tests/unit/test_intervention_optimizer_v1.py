from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.intervention_optimizer_v1 import (
    compute_optimized_intervention_score_v1,
    select_best_intervention_type,
)


def test_optimized_score_example_from_spec() -> None:
    score = compute_optimized_intervention_score_v1(
        intervention_score=Decimal("70"),
        historical_effectiveness=Decimal("20"),
    )
    assert score == Decimal("84.00")


def test_optimized_score_clamped_at_100() -> None:
    score = compute_optimized_intervention_score_v1(
        intervention_score=Decimal("95"),
        historical_effectiveness=Decimal("50"),
    )
    assert score == Decimal("100.00")


def test_select_best_intervention_type() -> None:
    best = select_best_intervention_type(
        {
            "REVISION_SPRINT": Decimal("78.2"),
            "WEAKNESS_REMEDIATION": Decimal("45.0"),
        }
    )
    assert best == ("REVISION_SPRINT", Decimal("78.2"))
