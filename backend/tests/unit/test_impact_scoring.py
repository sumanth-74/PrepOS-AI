from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.application.recommendations.impact_scoring import (
    CURRENT_AFFAIRS_WEIGHT,
    FORECAST_GAIN_WEIGHT,
    IMPACT_SCORE_MAX,
    PYQ_FREQUENCY_WEIGHT,
    WEAKNESS_WEIGHT,
    ImpactInputs,
    compute_impact,
    current_affairs_score_for_concept,
    estimate_readiness_gain,
    forecast_gain_score,
    normalize_score,
    pyq_frequency_score,
    recommendation_confidence,
)


def test_documented_weights_sum_to_one() -> None:
    total = WEAKNESS_WEIGHT + PYQ_FREQUENCY_WEIGHT + FORECAST_GAIN_WEIGHT + CURRENT_AFFAIRS_WEIGHT
    assert total == pytest.approx(1.0)


def test_normalize_score_clamps_to_0_100() -> None:
    assert normalize_score(None) == 0.0
    assert normalize_score(Decimal("-5")) == 0.0
    assert normalize_score(Decimal("150")) == 100.0
    assert normalize_score(Decimal("42.5")) == 42.5


def test_pyq_frequency_score_boosts_high_counts() -> None:
    base = pyq_frequency_score(frequency_score=50.0, pyq_count=0)
    mid = pyq_frequency_score(frequency_score=50.0, pyq_count=5)
    high = pyq_frequency_score(frequency_score=50.0, pyq_count=14)
    assert base == 50.0
    assert mid == 55.0
    assert high == 60.0


def test_compute_impact_is_deterministic_and_bounded() -> None:
    breakdown = compute_impact(
        ImpactInputs(
            weakness_score=80.0,
            pyq_frequency_score=70.0,
            forecast_gain_score=60.0,
            current_affairs_score=100.0,
        )
    )
    expected_weighted = (80 * 0.40) + (70 * 0.30) + (60 * 0.20) + (100 * 0.10)
    assert breakdown.impact_score == pytest.approx(min(IMPACT_SCORE_MAX, expected_weighted / 10.0), abs=0.01)
    assert breakdown.reason_codes == (
        "weakness",
        "high_pyq_frequency",
        "forecast_impact",
        "current_affairs_relevant",
    )


def test_current_affairs_score_for_known_concept() -> None:
    assert current_affairs_score_for_concept("upsc.polity_federalism") == 100.0
    assert current_affairs_score_for_concept("unknown_topic") == 0.0


def test_forecast_gain_score_blends_inputs() -> None:
    score = forecast_gain_score(
        readiness_gain=Decimal("40"),
        gap_to_goal=Decimal("30"),
        importance_score=Decimal("20"),
    )
    assert score == pytest.approx(33.0)


def test_estimate_readiness_gain_formula() -> None:
    gain = estimate_readiness_gain(impact_score=8.0, weakness_score=80.0)
    assert gain == pytest.approx(4.0)


def test_recommendation_confidence_thresholds() -> None:
    assert recommendation_confidence(impact_score=8.0, reason_count=2) == "high"
    assert recommendation_confidence(impact_score=6.0, reason_count=1) == "medium"
    assert recommendation_confidence(impact_score=3.0, reason_count=0) == "low"
