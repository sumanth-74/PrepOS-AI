from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.weakness_v1 import WeaknessInputs, compute_weakness_v1


def test_weakness_v1_excludes_null_retention_from_calculation() -> None:
    result = compute_weakness_v1(
        WeaknessInputs(
            mastery=Decimal("40"),
            retention=None,
            error_rate=Decimal("0.2"),
            confidence=Decimal("80"),
        )
    )

    assert result.unrated is False
    assert result.overconfident is True
    assert result.value == Decimal("61.43")


def test_weakness_v1_excludes_null_confidence_from_overconfidence() -> None:
    result = compute_weakness_v1(
        WeaknessInputs(
            mastery=Decimal("40"),
            retention=Decimal("30"),
            error_rate=Decimal("0.2"),
            confidence=None,
        )
    )

    assert result.unrated is False
    assert result.overconfident is False
    assert result.value == Decimal("57.00")


def test_weakness_v1_unrated_node_returns_none() -> None:
    result = compute_weakness_v1(
        WeaknessInputs(
            mastery=Decimal("0"),
            retention=None,
            confidence=None,
            unrated=True,
        )
    )

    assert result.value is None
    assert result.unrated is True
