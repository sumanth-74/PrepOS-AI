from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, redistribute_weights, round_score, weighted_blend

READINESS_V1_1 = "readiness_v1_1"

_W_KNOWLEDGE = Decimal("0.40")
_W_RETENTION = Decimal("0.30")
_W_CONFIDENCE = Decimal("0.20")
_W_COVERAGE = Decimal("0.10")

_DIMENSION_ORDER: tuple[str, ...] = ("knowledge", "retention", "confidence", "coverage")


@dataclass(frozen=True, slots=True)
class ReadinessInputsV1_1:  # noqa: N801
    average_mastery: Decimal | None
    average_retention: Decimal | None
    average_confidence: Decimal | None
    rated_node_count: int
    total_node_count: int


@dataclass(frozen=True, slots=True)
class ReadinessResultV1_1:  # noqa: N801
    overall_score: Decimal | None
    knowledge_subscore: Decimal | None
    retention_subscore: Decimal | None
    confidence_subscore: Decimal | None
    coverage_subscore: Decimal | None
    rated_node_count: int
    total_node_count: int
    unrated: bool
    version: str = READINESS_V1_1


def _round_subscore(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return round_score(clamp(value, Decimal("0"), Decimal("100")))


def compute_knowledge_subscore(average_mastery: Decimal | None) -> Decimal | None:
    return _round_subscore(average_mastery)


def compute_retention_subscore(average_retention: Decimal | None) -> Decimal | None:
    return _round_subscore(average_retention)


def compute_confidence_subscore(average_confidence: Decimal | None) -> Decimal | None:
    return _round_subscore(average_confidence)


def compute_coverage_subscore(*, rated_node_count: int, total_node_count: int) -> Decimal | None:
    if total_node_count == 0:
        return None
    raw = (Decimal(rated_node_count) / Decimal(total_node_count)) * Decimal("100")
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))


def compute_readiness_v1_1(inputs: ReadinessInputsV1_1) -> ReadinessResultV1_1:
    """Production readiness engine v1.1 with coverage and componentized subscores."""
    knowledge_subscore = compute_knowledge_subscore(inputs.average_mastery)
    retention_subscore = compute_retention_subscore(inputs.average_retention)
    confidence_subscore = compute_confidence_subscore(inputs.average_confidence)
    coverage_subscore = compute_coverage_subscore(
        rated_node_count=inputs.rated_node_count,
        total_node_count=inputs.total_node_count,
    )

    components: dict[str, Decimal] = {}
    base_weights: dict[str, Decimal] = {
        "knowledge": _W_KNOWLEDGE,
        "retention": _W_RETENTION,
        "confidence": _W_CONFIDENCE,
        "coverage": _W_COVERAGE,
    }
    counts: dict[str, int] = {}

    if knowledge_subscore is not None:
        components["knowledge"] = knowledge_subscore
        counts["knowledge"] = 1
    if retention_subscore is not None:
        components["retention"] = retention_subscore
        counts["retention"] = 1
    if confidence_subscore is not None:
        components["confidence"] = confidence_subscore
        counts["confidence"] = 1
    if coverage_subscore is not None:
        components["coverage"] = coverage_subscore
        counts["coverage"] = 1

    if not components:
        return ReadinessResultV1_1(
            overall_score=None,
            knowledge_subscore=knowledge_subscore,
            retention_subscore=retention_subscore,
            confidence_subscore=confidence_subscore,
            coverage_subscore=coverage_subscore,
            rated_node_count=inputs.rated_node_count,
            total_node_count=inputs.total_node_count,
            unrated=True,
        )

    weights = redistribute_weights(base_weights, counts)
    overall_score = round_score(weighted_blend(components, weights))

    return ReadinessResultV1_1(
        overall_score=overall_score,
        knowledge_subscore=knowledge_subscore,
        retention_subscore=retention_subscore,
        confidence_subscore=confidence_subscore,
        coverage_subscore=coverage_subscore,
        rated_node_count=inputs.rated_node_count,
        total_node_count=inputs.total_node_count,
        unrated=False,
    )
