from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import redistribute_weights
from prepos.domain.scoring.readiness_v1_1 import (
    _W_CONFIDENCE,
    _W_COVERAGE,
    _W_KNOWLEDGE,
    _W_RETENTION,
    ReadinessResultV1_1,
)

READINESS_DRIVERS_V1 = "readiness_drivers_v1"
_DIMENSION_ORDER: tuple[str, ...] = ("knowledge", "retention", "confidence", "coverage")


@dataclass(frozen=True, slots=True)
class ReadinessDriversV1:
    largest_positive_driver: str | None
    largest_negative_driver: str | None
    top_positive_drivers: tuple[str, ...]
    top_negative_drivers: tuple[str, ...]
    version: str = READINESS_DRIVERS_V1


def _subscore_for_dimension(result: ReadinessResultV1_1, dimension: str) -> Decimal | None:
    if dimension == "knowledge":
        return result.knowledge_subscore
    if dimension == "retention":
        return result.retention_subscore
    if dimension == "confidence":
        return result.confidence_subscore
    if dimension == "coverage":
        return result.coverage_subscore
    return None


def compute_readiness_drivers_v1(result: ReadinessResultV1_1) -> ReadinessDriversV1 | None:
    """Deterministic readiness driver ranking for Twin and dashboard surfaces."""
    if result.unrated:
        return None

    base_weights: dict[str, Decimal] = {
        "knowledge": _W_KNOWLEDGE,
        "retention": _W_RETENTION,
        "confidence": _W_CONFIDENCE,
        "coverage": _W_COVERAGE,
    }
    counts: dict[str, int] = {}
    subscores: dict[str, Decimal] = {}

    for dimension in _DIMENSION_ORDER:
        subscore = _subscore_for_dimension(result, dimension)
        if subscore is not None:
            subscores[dimension] = subscore
            counts[dimension] = 1

    weights = redistribute_weights(base_weights, counts)
    if not weights:
        return None

    positive_scores = {name: weights[name] * subscores[name] for name in weights}
    negative_scores = {name: weights[name] * (Decimal("100") - subscores[name]) for name in weights}

    max_positive = max(positive_scores.values())
    max_negative = max(negative_scores.values())

    largest_positive_driver = next(
        name for name in _DIMENSION_ORDER if positive_scores.get(name) == max_positive
    )
    largest_negative_driver = next(
        name for name in reversed(_DIMENSION_ORDER) if negative_scores.get(name) == max_negative
    )

    top_positive_drivers = tuple(
        name
        for name, _ in sorted(
            positive_scores.items(),
            key=lambda item: (-item[1], _DIMENSION_ORDER.index(item[0])),
        )
    )
    top_negative_drivers = tuple(
        name
        for name, _ in sorted(
            negative_scores.items(),
            key=lambda item: (-item[1], -_DIMENSION_ORDER.index(item[0])),
        )
    )

    return ReadinessDriversV1(
        largest_positive_driver=largest_positive_driver,
        largest_negative_driver=largest_negative_driver,
        top_positive_drivers=top_positive_drivers,
        top_negative_drivers=top_negative_drivers,
    )


def readiness_driver_context(result: ReadinessResultV1_1) -> dict[str, object]:
    """Compact driver context for recommendation explanations."""
    drivers = compute_readiness_drivers_v1(result)
    if drivers is None:
        return {"version": READINESS_DRIVERS_V1, "unrated": True}
    return {
        "version": READINESS_DRIVERS_V1,
        "unrated": False,
        "largest_positive_driver": drivers.largest_positive_driver,
        "largest_negative_driver": drivers.largest_negative_driver,
        "top_negative_drivers": list(drivers.top_negative_drivers),
        "coverage_subscore": float(result.coverage_subscore) if result.coverage_subscore is not None else None,
        "rated_node_count": result.rated_node_count,
        "total_node_count": result.total_node_count,
    }
