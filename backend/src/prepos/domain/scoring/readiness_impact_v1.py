from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score

READINESS_IMPACT_V1 = "readiness_impact_v1"

_W_IMPORTANCE = Decimal("0.50")
_W_WEAKNESS = Decimal("0.30")
_W_RETENTION_RISK = Decimal("0.20")

_MAX_READINESS_GAIN = Decimal("10")


@dataclass(frozen=True, slots=True)
class ReadinessImpactResult:
    readiness_gain: Decimal
    impact_score: Decimal
    confidence: Decimal


def compute_readiness_impact_v1(
    *,
    importance_score: Decimal,
    weakness_score: Decimal,
    retention_score: Decimal | None,
    recommendation_type: str,
) -> ReadinessImpactResult:
    """Heuristic readiness improvement estimate for a single concept recommendation."""
    del recommendation_type  # reserved for future type-specific tuning

    importance_factor = importance_score / Decimal("100")
    weakness_factor = weakness_score / Decimal("100")
    retention_risk_factor = (
        (Decimal("100") - retention_score) / Decimal("100")
        if retention_score is not None
        else Decimal("1")
    )

    impact_score = round_score(
        _W_IMPORTANCE * importance_factor
        + _W_WEAKNESS * weakness_factor
        + _W_RETENTION_RISK * retention_risk_factor,
        places=4,
    )
    readiness_gain = round_score(
        clamp(impact_score * Decimal("10"), Decimal("0"), _MAX_READINESS_GAIN),
    )

    confidence_base = Decimal("0.75") if retention_score is None else Decimal("0.85")
    confidence = round_score(
        clamp(confidence_base + impact_score * Decimal("0.10"), Decimal("0"), Decimal("1")),
    )

    return ReadinessImpactResult(
        readiness_gain=readiness_gain,
        impact_score=impact_score,
        confidence=confidence,
    )


def compute_total_estimated_gain(
    readiness_gains: tuple[Decimal, ...],
    *,
    top_n: int = 5,
) -> Decimal:
    """Sum readiness_gain for the top-N recommendations (already ranked)."""
    if not readiness_gains:
        return Decimal("0.00")
    selected = readiness_gains[:top_n]
    return round_score(sum(selected, start=Decimal("0")))
