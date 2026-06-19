from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.readiness_impact_v1 import (
    compute_readiness_impact_v1,
    compute_total_estimated_gain,
)


def test_readiness_impact_formula_with_retention() -> None:
    result = compute_readiness_impact_v1(
        importance_score=Decimal("80"),
        weakness_score=Decimal("70"),
        retention_score=Decimal("40"),
        recommendation_type="WEAKNESS_RECOVERY",
    )

    assert result.impact_score == Decimal("0.7300")
    assert result.readiness_gain == Decimal("7.30")
    assert result.confidence == Decimal("0.92")


def test_readiness_impact_null_retention_uses_full_risk_factor() -> None:
    result = compute_readiness_impact_v1(
        importance_score=Decimal("80"),
        weakness_score=Decimal("70"),
        retention_score=None,
        recommendation_type="REVISION_DUE",
    )

    assert result.impact_score == Decimal("0.8100")
    assert result.readiness_gain == Decimal("8.10")
    assert result.confidence == Decimal("0.83")


def test_readiness_gain_clamped_to_ten_points() -> None:
    result = compute_readiness_impact_v1(
        importance_score=Decimal("100"),
        weakness_score=Decimal("100"),
        retention_score=Decimal("0"),
        recommendation_type="HIGH_IMPORTANCE_GAP",
    )

    assert result.readiness_gain == Decimal("10.00")


def test_total_estimated_gain_sums_top_five() -> None:
    gains = tuple(Decimal(str(value)) for value in (3.5, 2.8, 2.1, 1.5, 1.0, 0.5))
    assert compute_total_estimated_gain(gains) == Decimal("10.90")
    assert compute_total_estimated_gain(gains, top_n=3) == Decimal("8.40")
