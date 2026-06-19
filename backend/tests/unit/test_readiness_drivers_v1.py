from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.readiness_drivers_v1 import compute_readiness_drivers_v1
from prepos.domain.scoring.readiness_v1_1 import ReadinessInputsV1_1, compute_readiness_v1_1


def test_driver_ranking_returns_top_lists() -> None:
    result = compute_readiness_v1_1(
        ReadinessInputsV1_1(
            average_mastery=Decimal("82"),
            average_retention=Decimal("90"),
            average_confidence=Decimal("70"),
            rated_node_count=10,
            total_node_count=500,
        )
    )
    drivers = compute_readiness_drivers_v1(result)

    assert drivers is not None
    assert drivers.largest_positive_driver == "knowledge"
    assert drivers.largest_negative_driver == "coverage"
    assert drivers.top_positive_drivers[0] == "knowledge"
    assert "coverage" in drivers.top_negative_drivers


def test_driver_ranking_unrated_returns_none() -> None:
    result = compute_readiness_v1_1(
        ReadinessInputsV1_1(
            average_mastery=None,
            average_retention=None,
            average_confidence=None,
            rated_node_count=0,
            total_node_count=0,
        )
    )

    assert compute_readiness_drivers_v1(result) is None
