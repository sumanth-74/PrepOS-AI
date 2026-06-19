from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.recommendations_v1 import explain_recommendation
from prepos.domain.twin.value_objects import RecommendationType


def test_high_importance_gap_explanation() -> None:
    explanation = explain_recommendation(
        RecommendationType.HIGH_IMPORTANCE_GAP,
        readiness_gain=Decimal("5.00"),
    )
    assert explanation == "This important concept is underperforming and could significantly increase readiness."


def test_readiness_boost_explanation() -> None:
    explanation = explain_recommendation(
        RecommendationType.READINESS_BOOST,
        readiness_gain=Decimal("2.50"),
    )
    assert explanation == "This concept offers incremental readiness improvement."
