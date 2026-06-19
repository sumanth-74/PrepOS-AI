from __future__ import annotations

from decimal import Decimal

from prepos.domain.revision_queue.priority_v1 import compute_priority_v1, compute_retention_risk


def test_priority_formula() -> None:
    score = compute_priority_v1(
        importance_score=Decimal("90"),
        weakness_score=Decimal("78"),
        retention_score=Decimal("35"),
    )
    expected = (
        Decimal("0.40") * Decimal("90")
        + Decimal("0.35") * Decimal("78")
        + Decimal("0.25") * compute_retention_risk(Decimal("35"))
    )
    assert score == expected.quantize(Decimal("0.01"))


def test_priority_null_retention_uses_full_risk() -> None:
    score = compute_priority_v1(
        importance_score=Decimal("50"),
        weakness_score=Decimal("40"),
        retention_score=None,
    )
    assert score == Decimal("59.00")
