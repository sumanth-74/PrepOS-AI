from __future__ import annotations

from decimal import Decimal

import pytest

from prepos.domain.scoring.common import (
    clamp,
    logistic,
    norm,
    recency_weight,
    redistribute_weights,
    round_score,
    shrink,
    weighted_blend,
)


def test_clamp_bounds() -> None:
    assert clamp(Decimal("5"), Decimal("0"), Decimal("10")) == Decimal("5")
    assert clamp(Decimal("-1"), Decimal("0"), Decimal("10")) == Decimal("0")
    assert clamp(Decimal("11"), Decimal("0"), Decimal("10")) == Decimal("10")


def test_norm_handles_equal_bounds_and_range() -> None:
    assert norm(Decimal("5"), Decimal("5"), Decimal("5")) == Decimal("0")
    assert norm(Decimal("7"), Decimal("5"), Decimal("10")) == Decimal("0.4")


def test_logistic_squashes_to_unit_interval() -> None:
    assert logistic(Decimal("0"), Decimal("0"), Decimal("1")) == Decimal("0.5")


def test_shrink_applies_prior_and_rejects_negative_evidence() -> None:
    assert shrink(Decimal("1"), 0, Decimal("5"), Decimal("0.2")) == Decimal("0.2")
    assert shrink(Decimal("1"), 0, Decimal("0"), Decimal("0.3")) == Decimal("0.3")
    with pytest.raises(ValueError, match="non-negative"):
        shrink(Decimal("1"), -1, Decimal("5"), Decimal("0.2"))


def test_round_score_half_up() -> None:
    assert round_score(Decimal("1.005")) == Decimal("1.01")


def test_recency_weight_decay_and_edge_cases() -> None:
    assert recency_weight(Decimal("0"), Decimal("30")) == Decimal("1")
    assert recency_weight(Decimal("30"), Decimal("0")) == Decimal("0")
    assert recency_weight(Decimal("30"), Decimal("30")) == Decimal("0.5")


def test_redistribute_weights_renormalizes_active_components() -> None:
    weights = {"mcq": Decimal("0.5"), "mains": Decimal("0.5")}
    counts = {"mcq": 1, "mains": 0}
    assert redistribute_weights(weights, counts) == {"mcq": Decimal("1")}


def test_redistribute_weights_returns_empty_when_no_evidence() -> None:
    weights = {"mcq": Decimal("0.5"), "mains": Decimal("0.5")}
    counts = {"mcq": 0, "mains": 0}
    assert redistribute_weights(weights, counts) == {}


def test_redistribute_weights_returns_empty_when_total_weight_zero() -> None:
    weights = {"mcq": Decimal("0"), "mains": Decimal("0")}
    counts = {"mcq": 1, "mains": 1}
    assert redistribute_weights(weights, counts) == {}


def test_weighted_blend_sums_weighted_components() -> None:
    components = {"mcq": Decimal("0.8"), "mains": Decimal("0.4")}
    weights = {"mcq": Decimal("0.75"), "mains": Decimal("0.25")}
    assert weighted_blend(components, weights) == Decimal("0.7")
