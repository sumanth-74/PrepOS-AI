from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, redistribute_weights, round_score, weighted_blend
from prepos.domain.scoring.config import DEFAULT_SCORING_CONFIG, ScoringConfig

READINESS_V1 = "readiness_v1"

_W_MASTERY = Decimal("0.50")
_W_RETENTION = Decimal("0.30")
_W_CONFIDENCE = Decimal("0.20")

_IMPROVEMENT_MESSAGES: dict[str, str] = {
    "mastery": "Focused practice on weak concepts would increase readiness fastest.",
    "retention": "Revision completion would increase readiness fastest.",
    "confidence": "Additional assessed practice with self-reflection would increase readiness fastest.",
}

_DIMENSION_ORDER: tuple[str, ...] = ("mastery", "retention", "confidence")


@dataclass(frozen=True, slots=True)
class ReadinessInputs:
    """Snapshot-level readiness inputs (S5.3 LG v1)."""

    average_mastery: Decimal | None
    average_retention: Decimal | None
    average_confidence: Decimal | None


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    score: Decimal | None
    mastery_subscore: Decimal | None
    retention_subscore: Decimal | None
    confidence_subscore: Decimal | None
    unrated: bool
    version: str = READINESS_V1


@dataclass(frozen=True, slots=True)
class ReadinessExplanation:
    strongest_dimension: str
    weakest_dimension: str
    improvement_opportunity: str


def _round_subscore(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return round_score(clamp(value, Decimal("0"), Decimal("100")))


def compute_readiness_v1(
    inputs: ReadinessInputs,
    *,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> ReadinessResult:
    """Compute headline readiness from LG snapshot aggregates (S5.3)."""
    _ = config

    mastery_subscore = _round_subscore(inputs.average_mastery)
    retention_subscore = _round_subscore(inputs.average_retention)
    confidence_subscore = _round_subscore(inputs.average_confidence)

    if mastery_subscore is None and retention_subscore is None and confidence_subscore is None:
        return ReadinessResult(
            score=None,
            mastery_subscore=None,
            retention_subscore=None,
            confidence_subscore=None,
            unrated=True,
        )

    components: dict[str, Decimal] = {}
    base_weights: dict[str, Decimal] = {
        "mastery": _W_MASTERY,
        "retention": _W_RETENTION,
        "confidence": _W_CONFIDENCE,
    }
    counts: dict[str, int] = {}

    if mastery_subscore is not None:
        components["mastery"] = mastery_subscore
        counts["mastery"] = 1
    if retention_subscore is not None:
        components["retention"] = retention_subscore
        counts["retention"] = 1
    if confidence_subscore is not None:
        components["confidence"] = confidence_subscore
        counts["confidence"] = 1

    weights = redistribute_weights(base_weights, counts)
    score = round_score(weighted_blend(components, weights))

    return ReadinessResult(
        score=score,
        mastery_subscore=mastery_subscore,
        retention_subscore=retention_subscore,
        confidence_subscore=confidence_subscore,
        unrated=False,
    )


def compute_readiness_explanation(result: ReadinessResult) -> ReadinessExplanation | None:
    """Deterministic Twin explanation from readiness subscores."""
    if result.unrated:
        return None

    present: dict[str, Decimal] = {}
    if result.mastery_subscore is not None:
        present["mastery"] = result.mastery_subscore
    if result.retention_subscore is not None:
        present["retention"] = result.retention_subscore
    if result.confidence_subscore is not None:
        present["confidence"] = result.confidence_subscore

    if not present:
        return None

    max_score = max(present.values())
    min_score = min(present.values())

    strongest_candidates = [name for name in _DIMENSION_ORDER if present.get(name) == max_score]
    weakest_candidates = [name for name in reversed(_DIMENSION_ORDER) if present.get(name) == min_score]

    strongest_dimension = strongest_candidates[0]
    weakest_dimension = weakest_candidates[0]

    return ReadinessExplanation(
        strongest_dimension=strongest_dimension,
        weakest_dimension=weakest_dimension,
        improvement_opportunity=_IMPROVEMENT_MESSAGES[weakest_dimension],
    )
