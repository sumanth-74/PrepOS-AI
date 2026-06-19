from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.common import clamp

ADAPTIVE_CAPACITY_V1 = "adaptive_capacity_v1"

_MIN_CAPACITY = 30
_MAX_CAPACITY = 300


def compute_adaptive_capacity_v1(
    *,
    base_capacity_minutes: int,
    gap_to_goal: Decimal,
    on_track: bool,
) -> int:
    """Scale daily study capacity based on goal gap."""
    capacity = Decimal(base_capacity_minutes)
    if gap_to_goal > Decimal("20"):
        capacity *= Decimal("1.5")
    elif gap_to_goal > Decimal("10"):
        capacity *= Decimal("1.25")
    elif on_track:
        capacity *= Decimal("1.0")

    clamped = clamp(capacity, Decimal(_MIN_CAPACITY), Decimal(_MAX_CAPACITY))
    return int(clamped.to_integral_value())
