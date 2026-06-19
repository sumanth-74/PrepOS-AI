from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from prepos.domain.goal.milestone_explanations_v1 import explain_milestone_status_v1
from prepos.domain.goal.milestones_v1 import (
    MilestoneGenerationInputs,
    MilestoneStatus,
    classify_milestone_status,
    compute_milestone_status_v1,
    generate_milestones_v1,
    resolve_current_milestone,
    resolve_next_milestone,
)
from prepos.domain.goal.trajectory_v1 import compute_goal_trajectory_v1


def test_trajectory_formula() -> None:
    result = compute_goal_trajectory_v1(
        current_readiness=Decimal("70.50"),
        target_readiness=Decimal("85"),
        days_remaining=60,
    )
    assert result.required_gain == Decimal("14.50")
    assert result.expected_daily_progress == Decimal("0.24")
    assert result.expected_weekly_progress == Decimal("1.68")


def test_trajectory_uses_minimum_one_day_divisor() -> None:
    result = compute_goal_trajectory_v1(
        current_readiness=Decimal("80"),
        target_readiness=Decimal("85"),
        days_remaining=0,
    )
    assert result.required_gain == Decimal("5.00")
    assert result.expected_daily_progress == Decimal("5.00")
    assert result.expected_weekly_progress == Decimal("35.00")


def test_milestone_generation_every_seven_days() -> None:
    milestones = generate_milestones_v1(
        MilestoneGenerationInputs(
            current_readiness=Decimal("60"),
            target_readiness=Decimal("85"),
            target_date=date(2026, 8, 17),
            current_time=datetime(2026, 6, 18, tzinfo=UTC),
            coverage_subscore=Decimal("50"),
            confidence_subscore=Decimal("70"),
        )
    )
    assert len(milestones) == 9
    assert milestones[0].target_date == date(2026, 6, 25)
    assert milestones[-1].target_date == date(2026, 8, 17)
    assert milestones[-1].target_readiness == Decimal("85.00")
    assert milestones[0].target_readiness == Decimal("62.92")


def test_milestone_status_classification() -> None:
    assert classify_milestone_status(
        actual_readiness=Decimal("80"),
        milestone_target=Decimal("75"),
    ) == MilestoneStatus.AHEAD
    assert classify_milestone_status(
        actual_readiness=Decimal("76"),
        milestone_target=Decimal("75"),
    ) == MilestoneStatus.ON_TRACK
    assert classify_milestone_status(
        actual_readiness=Decimal("70"),
        milestone_target=Decimal("75"),
    ) == MilestoneStatus.BEHIND


def test_compute_milestone_status_uses_next_upcoming_milestone() -> None:
    milestones = generate_milestones_v1(
        MilestoneGenerationInputs(
            current_readiness=Decimal("60"),
            target_readiness=Decimal("85"),
            target_date=date(2026, 8, 17),
            current_time=datetime(2026, 6, 18, tzinfo=UTC),
            coverage_subscore=Decimal("50"),
            confidence_subscore=Decimal("70"),
        )
    )
    current = datetime(2026, 6, 18, tzinfo=UTC)
    assert resolve_current_milestone(milestones, current_time=current) == milestones[0]
    assert resolve_next_milestone(milestones, current_time=current) == milestones[0]

    status = compute_milestone_status_v1(
        actual_readiness=Decimal("58"),
        milestones=milestones,
        current_time=current,
    )
    assert status.status == MilestoneStatus.BEHIND
    assert status.current_gap == Decimal("4.92")


def test_milestone_explanations_are_deterministic() -> None:
    behind = explain_milestone_status_v1(
        status=MilestoneStatus.BEHIND,
        current_gap=Decimal("3.50"),
    )
    assert behind == "You are 3.5 readiness points behind the current milestone."

    ahead = explain_milestone_status_v1(
        status=MilestoneStatus.AHEAD,
        current_gap=Decimal("-4.20"),
    )
    assert ahead == "You are ahead of schedule by 4.2 readiness points."

    on_track = explain_milestone_status_v1(
        status=MilestoneStatus.ON_TRACK,
        current_gap=Decimal("0.50"),
    )
    assert on_track == "Maintaining your current study plan keeps you on track."
