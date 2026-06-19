from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import redistribute_weights
from prepos.domain.scoring.readiness_v1 import ReadinessInputs, ReadinessResult

READINESS_EXPLANATION_V1 = "readiness_explanation_v1"

_W_MASTERY = Decimal("0.50")
_W_RETENTION = Decimal("0.30")
_W_CONFIDENCE = Decimal("0.20")

_DIMENSION_ORDER: tuple[str, ...] = ("mastery", "retention", "confidence")


@dataclass(frozen=True, slots=True)
class ReadinessDrivers:
    largest_positive_driver: str | None
    largest_negative_driver: str | None
    version: str = READINESS_EXPLANATION_V1


def compute_readiness_drivers_v1(
    result: ReadinessResult,
    inputs: ReadinessInputs,
) -> ReadinessDrivers | None:
    """Weighted positive/negative readiness drivers for Twin snapshot."""
    _ = result
    if inputs.average_mastery is None and inputs.average_retention is None and inputs.average_confidence is None:
        return None

    values: dict[str, Decimal] = {}
    base_weights: dict[str, Decimal] = {
        "mastery": _W_MASTERY,
        "retention": _W_RETENTION,
        "confidence": _W_CONFIDENCE,
    }
    counts: dict[str, int] = {}

    if inputs.average_mastery is not None:
        values["mastery"] = inputs.average_mastery
        counts["mastery"] = 1
    if inputs.average_retention is not None:
        values["retention"] = inputs.average_retention
        counts["retention"] = 1
    if inputs.average_confidence is not None:
        values["confidence"] = inputs.average_confidence
        counts["confidence"] = 1

    weights = redistribute_weights(base_weights, counts)
    if not weights:
        return None

    positive_scores = {name: weights[name] * values[name] for name in weights}
    negative_scores = {name: weights[name] * (Decimal("100") - values[name]) for name in weights}

    max_positive = max(positive_scores.values())
    max_negative = max(negative_scores.values())

    positive_driver = next(
        name for name in _DIMENSION_ORDER if positive_scores.get(name) == max_positive
    )
    negative_driver = next(
        name for name in reversed(_DIMENSION_ORDER) if negative_scores.get(name) == max_negative
    )

    return ReadinessDrivers(
        largest_positive_driver=positive_driver,
        largest_negative_driver=negative_driver,
    )
