from __future__ import annotations

from datetime import UTC, datetime

import pytest

from prepos.application.memory.milestone_detection import (
    detect_forecast_milestone,
    detect_goal_milestone,
    detect_readiness_milestones,
    detect_weakness_resolved_milestone,
)


def test_readiness_plus_ten_milestone() -> None:
    now = datetime.now(UTC)
    milestones = detect_readiness_milestones(
        previous_readiness=40.0,
        current_readiness=52.0,
        occurred_at=now,
    )
    thresholds = {item.memory_value["threshold"] for item in milestones}
    assert thresholds == {5, 10}


def test_weakness_resolved_milestone() -> None:
    now = datetime.now(UTC)
    milestone = detect_weakness_resolved_milestone(
        concept_id="upsc.polity_federalism",
        weakness_before=75.0,
        weakness_after=35.0,
        occurred_at=now,
    )
    assert milestone is not None
    assert milestone.memory_value["milestone_type"] == "weakness_resolved"


def test_forecast_target_milestone() -> None:
    now = datetime.now(UTC)
    milestone = detect_forecast_milestone(
        forecast_before=58.0,
        forecast_after=62.0,
        target=60.0,
        occurred_at=now,
    )
    assert milestone is not None
