from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, redistribute_weights, round_score, weighted_blend
from prepos.domain.scoring.config import DEFAULT_SCORING_CONFIG, ScoringConfig

WEAKNESS_V1 = "weakness_v1"


@dataclass(frozen=True, slots=True)
class WeaknessInputs:
    mastery: Decimal
    retention: Decimal | None = None
    error_rate: Decimal = Decimal("0")
    confidence: Decimal | None = None
    unrated: bool = False


@dataclass(frozen=True, slots=True)
class WeaknessResult:
    value: Decimal | None
    version: str
    weakness_unit: Decimal | None
    overconfident: bool
    unrated: bool


def is_overconfident(
    *,
    mastery: Decimal,
    confidence: Decimal | None,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> bool:
    """Overconfidence flag (spec §5.5 / v1.1 §2.4)."""
    if confidence is None:
        return False
    return (
        confidence - mastery >= config.WEAK_OVERCONFIDENCE_GAP
        and mastery < config.WEAK_OVERCONFIDENCE_MASTERY_CEILING
    )


def compute_weakness_v1(
    inputs: WeaknessInputs,
    *,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> WeaknessResult:
    """On-demand weakness from mastery, retention, and confidence (spec §5.5)."""
    if inputs.unrated:
        return WeaknessResult(
            value=None,
            version=WEAKNESS_V1,
            weakness_unit=None,
            overconfident=False,
            unrated=True,
        )

    mastery = clamp(inputs.mastery, Decimal("0"), Decimal("100"))
    error_norm = clamp(inputs.error_rate, Decimal("0"), Decimal("1"))

    component_values: dict[str, Decimal] = {
        "mastery": (Decimal("100") - mastery) / Decimal("100"),
        "error": error_norm,
    }
    base_weights: dict[str, Decimal] = {
        "mastery": config.WEAK_W_MASTERY,
        "error": config.WEAK_W_ERROR,
    }
    component_counts: dict[str, int] = {"mastery": 1, "error": 1}

    if inputs.retention is not None:
        retention = clamp(inputs.retention, Decimal("0"), Decimal("100"))
        component_values["retention"] = (Decimal("100") - retention) / Decimal("100")
        base_weights["retention"] = config.WEAK_W_RETENTION
        component_counts["retention"] = 1

    redistributed = redistribute_weights(base_weights, component_counts)
    weakness_unit = weighted_blend(component_values, redistributed)

    overconfident = is_overconfident(mastery=mastery, confidence=inputs.confidence, config=config)
    bonus = config.WEAK_OVERCONF_BONUS if overconfident else Decimal("0")
    weakness = clamp(Decimal("100") * weakness_unit + bonus, Decimal("0"), Decimal("100"))

    return WeaknessResult(
        value=round_score(weakness),
        version=WEAKNESS_V1,
        weakness_unit=weakness_unit,
        overconfident=overconfident,
        unrated=False,
    )
