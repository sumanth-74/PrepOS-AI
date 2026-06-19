from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import round_score

GOAL_TRAJECTORY_V1 = "goal_trajectory_v1"


@dataclass(frozen=True, slots=True)
class GoalTrajectoryResult:
    required_gain: Decimal
    expected_daily_progress: Decimal
    expected_weekly_progress: Decimal


def compute_goal_trajectory_v1(
    *,
    current_readiness: Decimal,
    target_readiness: Decimal,
    days_remaining: int,
) -> GoalTrajectoryResult:
    """Required gain spread evenly over remaining days until the goal date."""
    required_gain = round_score(max(target_readiness - current_readiness, Decimal("0")))
    divisor = max(days_remaining, 1)
    expected_daily_progress = round_score(required_gain / Decimal(divisor))
    expected_weekly_progress = round_score(expected_daily_progress * Decimal("7"))
    return GoalTrajectoryResult(
        required_gain=required_gain,
        expected_daily_progress=expected_daily_progress,
        expected_weekly_progress=expected_weekly_progress,
    )
