from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score

READINESS_FORECAST_V1 = "readiness_forecast_v1"

_DAILY_GAIN_CAP = Decimal("0.5")


@dataclass(frozen=True, slots=True)
class ReadinessForecastInputs:
    current_readiness: Decimal
    total_estimated_gain: Decimal
    target_readiness_score: Decimal
    target_date: date
    current_time: datetime


@dataclass(frozen=True, slots=True)
class ReadinessForecastResult:
    current_readiness: Decimal
    projected_readiness: Decimal
    gap_to_goal: Decimal
    on_track: bool
    days_remaining: int


def compute_days_remaining(*, target_date: date, current_time: datetime) -> int:
    today = current_time.date()
    delta = (target_date - today).days
    return max(delta, 0)


def compute_readiness_forecast_v1(inputs: ReadinessForecastInputs) -> ReadinessForecastResult:
    """Project readiness at target date using capped daily improvement."""
    days_remaining = compute_days_remaining(
        target_date=inputs.target_date,
        current_time=inputs.current_time,
    )
    capped_gain = min(
        inputs.total_estimated_gain,
        Decimal(days_remaining) * _DAILY_GAIN_CAP,
    )
    projected = round_score(
        clamp(
            inputs.current_readiness + capped_gain,
            Decimal("0"),
            Decimal("100"),
        )
    )
    on_track = projected >= inputs.target_readiness_score
    gap_to_goal = round_score(
        max(inputs.target_readiness_score - projected, Decimal("0")),
    )
    return ReadinessForecastResult(
        current_readiness=round_score(inputs.current_readiness),
        projected_readiness=projected,
        gap_to_goal=gap_to_goal,
        on_track=on_track,
        days_remaining=days_remaining,
    )
