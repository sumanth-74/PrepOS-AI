from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.readiness_explanation_v1 import compute_readiness_drivers_v1
from prepos.domain.scoring.readiness_v1 import ReadinessInputs, ReadinessResult


def test_readiness_driver_calculation() -> None:
    inputs = ReadinessInputs(
        average_mastery=Decimal("80"),
        average_retention=Decimal("60"),
        average_confidence=Decimal("70"),
    )
    result = ReadinessResult(
        score=Decimal("72.00"),
        mastery_subscore=Decimal("80.00"),
        retention_subscore=Decimal("60.00"),
        confidence_subscore=Decimal("70.00"),
        unrated=False,
    )
    drivers = compute_readiness_drivers_v1(result, inputs)

    assert drivers is not None
    assert drivers.largest_positive_driver == "mastery"
    assert drivers.largest_negative_driver == "retention"


def test_readiness_drivers_all_null() -> None:
    result = ReadinessResult(
        score=None,
        mastery_subscore=None,
        retention_subscore=None,
        confidence_subscore=None,
        unrated=True,
    )
    inputs = ReadinessInputs(
        average_mastery=None,
        average_retention=None,
        average_confidence=None,
    )
    assert compute_readiness_drivers_v1(result, inputs) is None
