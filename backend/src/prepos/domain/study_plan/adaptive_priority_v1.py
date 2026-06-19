from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score

ADAPTIVE_PRIORITY_V1 = "adaptive_priority_v1"

_COMPLETION_DAMPING = Decimal("0.25")


def compute_adaptive_priority_v1(
    *,
    priority_score: Decimal,
    completion_rate: Decimal,
    skip_rate: Decimal,
) -> Decimal:
    """Adaptive urgency from base priority and per-concept execution history."""
    adaptive = priority_score * (Decimal("1") + skip_rate) * (
        Decimal("1") - completion_rate * _COMPLETION_DAMPING
    )
    return round_score(clamp(adaptive, Decimal("0"), Decimal("100")))
