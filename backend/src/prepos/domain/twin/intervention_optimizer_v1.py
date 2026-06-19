from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score

_OPTIMIZER_MIN = Decimal("0")
_OPTIMIZER_MAX = Decimal("100")


@dataclass(frozen=True, slots=True)
class InterventionOptimizationResult:
    optimized_score: Decimal
    historical_effectiveness: Decimal


def compute_optimized_intervention_score_v1(
    *,
    intervention_score: Decimal,
    historical_effectiveness: Decimal,
) -> Decimal:
    multiplier = Decimal("1") + historical_effectiveness / Decimal("100")
    raw = intervention_score * multiplier
    return round_score(clamp(raw, _OPTIMIZER_MIN, _OPTIMIZER_MAX))


def select_best_intervention_type(
    effectiveness_by_type: dict[str, Decimal],
) -> tuple[str, Decimal] | None:
    if not effectiveness_by_type:
        return None
    best_type = max(effectiveness_by_type, key=lambda item: effectiveness_by_type[item])
    return best_type, effectiveness_by_type[best_type]
