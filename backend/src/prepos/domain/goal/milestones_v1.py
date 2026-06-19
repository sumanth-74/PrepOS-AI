from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from prepos.domain.scoring.common import clamp, round_score
from prepos.domain.scoring.predicted_score_v1 import PredictedScoreInputs, compute_predicted_score_v1

MILESTONES_V1 = "milestones_v1"
_MILESTONE_INTERVAL_DAYS = 7
_STATUS_TOLERANCE = Decimal("2")


class MilestoneStatus(StrEnum):
    AHEAD = "AHEAD"
    ON_TRACK = "ON_TRACK"
    BEHIND = "BEHIND"


@dataclass(frozen=True, slots=True)
class Milestone:
    target_date: date
    target_readiness: Decimal
    expected_score: Decimal


@dataclass(frozen=True, slots=True)
class MilestoneStatusResult:
    status: MilestoneStatus
    current_gap: Decimal
    current_milestone: Milestone | None


@dataclass(frozen=True, slots=True)
class MilestoneGenerationInputs:
    current_readiness: Decimal
    target_readiness: Decimal
    target_date: date
    current_time: datetime
    coverage_subscore: Decimal | None
    confidence_subscore: Decimal | None


def _interpolate_readiness(
    *,
    current_readiness: Decimal,
    target_readiness: Decimal,
    days_elapsed: int,
    total_days: int,
) -> Decimal:
    if total_days <= 0:
        return round_score(clamp(target_readiness, Decimal("0"), Decimal("100")))
    fraction = Decimal(days_elapsed) / Decimal(total_days)
    interpolated = current_readiness + (target_readiness - current_readiness) * fraction
    return round_score(clamp(interpolated, Decimal("0"), Decimal("100")))


def _expected_score_for_readiness(
    *,
    target_readiness: Decimal,
    coverage_subscore: Decimal | None,
    confidence_subscore: Decimal | None,
) -> Decimal:
    score = compute_predicted_score_v1(
        PredictedScoreInputs(
            readiness_score=target_readiness,
            coverage_subscore=coverage_subscore,
            confidence_subscore=confidence_subscore,
        )
    )
    if score is None:
        return target_readiness
    return score


def generate_milestones_v1(inputs: MilestoneGenerationInputs) -> tuple[Milestone, ...]:
    """Weekly milestones linearly interpolated from current readiness to the goal."""
    today = inputs.current_time.date()
    if inputs.target_date <= today:
        expected_score = _expected_score_for_readiness(
            target_readiness=inputs.target_readiness,
            coverage_subscore=inputs.coverage_subscore,
            confidence_subscore=inputs.confidence_subscore,
        )
        return (
            Milestone(
                target_date=inputs.target_date,
                target_readiness=round_score(inputs.target_readiness),
                expected_score=expected_score,
            ),
        )

    total_days = (inputs.target_date - today).days
    milestone_dates: list[date] = []
    offset = _MILESTONE_INTERVAL_DAYS
    while offset < total_days:
        milestone_dates.append(today + timedelta(days=offset))
        offset += _MILESTONE_INTERVAL_DAYS
    milestone_dates.append(inputs.target_date)

    milestones: list[Milestone] = []
    for milestone_date in milestone_dates:
        days_elapsed = (milestone_date - today).days
        target_readiness = _interpolate_readiness(
            current_readiness=inputs.current_readiness,
            target_readiness=inputs.target_readiness,
            days_elapsed=days_elapsed,
            total_days=total_days,
        )
        expected_score = _expected_score_for_readiness(
            target_readiness=target_readiness,
            coverage_subscore=inputs.coverage_subscore,
            confidence_subscore=inputs.confidence_subscore,
        )
        milestones.append(
            Milestone(
                target_date=milestone_date,
                target_readiness=target_readiness,
                expected_score=expected_score,
            )
        )
    return tuple(milestones)


def resolve_current_milestone(
    milestones: tuple[Milestone, ...],
    *,
    current_time: datetime,
) -> Milestone | None:
    if not milestones:
        return None
    today = current_time.date()
    upcoming = [milestone for milestone in milestones if milestone.target_date >= today]
    if upcoming:
        return upcoming[0]
    return milestones[-1]


def classify_milestone_status(
    *,
    actual_readiness: Decimal,
    milestone_target: Decimal,
) -> MilestoneStatus:
    if actual_readiness > milestone_target + _STATUS_TOLERANCE:
        return MilestoneStatus.AHEAD
    if actual_readiness < milestone_target - _STATUS_TOLERANCE:
        return MilestoneStatus.BEHIND
    return MilestoneStatus.ON_TRACK


def compute_milestone_status_v1(
    *,
    actual_readiness: Decimal,
    milestones: tuple[Milestone, ...],
    current_time: datetime,
) -> MilestoneStatusResult:
    current_milestone = resolve_current_milestone(milestones, current_time=current_time)
    if current_milestone is None:
        return MilestoneStatusResult(
            status=MilestoneStatus.ON_TRACK,
            current_gap=Decimal("0.00"),
            current_milestone=None,
        )

    status = classify_milestone_status(
        actual_readiness=actual_readiness,
        milestone_target=current_milestone.target_readiness,
    )
    current_gap = round_score(current_milestone.target_readiness - actual_readiness)
    return MilestoneStatusResult(
        status=status,
        current_gap=current_gap,
        current_milestone=current_milestone,
    )


def resolve_next_milestone(
    milestones: tuple[Milestone, ...],
    *,
    current_time: datetime,
) -> Milestone | None:
    today = current_time.date()
    for milestone in milestones:
        if milestone.target_date >= today:
            return milestone
    return None
