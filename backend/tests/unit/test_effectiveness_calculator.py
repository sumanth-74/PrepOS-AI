from __future__ import annotations

import pytest

from prepos.application.recommendations.outcomes.effectiveness_calculator import (
    EFFECTIVENESS_SCORE_MAX,
    calculate_actual_gain,
    calculate_effectiveness_score,
    outcome_status,
)


@pytest.mark.parametrize(
    ("predicted", "actual", "expected"),
    [
        (2.0, 2.0, 1.0),
        (2.0, 4.0, 2.0),
        (4.0, 1.0, 0.25),
        (0.0, 3.0, 0.0),
        (-1.0, 5.0, 0.0),
    ],
)
def test_calculate_effectiveness_score(predicted: float, actual: float, expected: float) -> None:
    assert calculate_effectiveness_score(actual_gain=actual, predicted_gain=predicted) == expected


def test_calculate_effectiveness_score_is_clamped_to_three() -> None:
    score = calculate_effectiveness_score(actual_gain=20.0, predicted_gain=1.0)
    assert score == EFFECTIVENESS_SCORE_MAX


def test_calculate_actual_gain() -> None:
    assert calculate_actual_gain(readiness_before=55.0, readiness_after=59.1) == 4.1


@pytest.mark.parametrize(
    ("effectiveness", "actual", "expected"),
    [
        (1.37, 4.1, "successful"),
        (0.75, 1.0, "partial"),
        (0.25, 0.5, "failed"),
    ],
)
def test_outcome_status(effectiveness: float, actual: float, expected: str) -> None:
    assert outcome_status(effectiveness_score=effectiveness, actual_gain=actual) == expected
