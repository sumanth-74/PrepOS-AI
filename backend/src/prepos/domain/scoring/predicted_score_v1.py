from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from prepos.domain.scoring.common import clamp, redistribute_weights, round_score, weighted_blend

PREDICTED_SCORE_V1 = "predicted_score_v1"

_W_READINESS = Decimal("0.70")
_W_COVERAGE = Decimal("0.20")
_W_CONFIDENCE = Decimal("0.10")

_MIN_UNCERTAINTY = Decimal("5")
_UNCERTAINTY_FACTOR = Decimal("0.20")


class PreparationRisk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True, slots=True)
class PredictedScoreInputs:
    readiness_score: Decimal | None
    coverage_subscore: Decimal | None
    confidence_subscore: Decimal | None


@dataclass(frozen=True, slots=True)
class PredictedScoreRange:
    low_score: Decimal
    expected_score: Decimal
    high_score: Decimal


def compute_predicted_score_v1(inputs: PredictedScoreInputs) -> Decimal | None:
    """Weighted readiness/coverage/confidence blend with v1.1 redistribution."""
    components: dict[str, Decimal] = {}
    counts: dict[str, int] = {}
    base_weights: dict[str, Decimal] = {
        "readiness": _W_READINESS,
        "coverage": _W_COVERAGE,
        "confidence": _W_CONFIDENCE,
    }

    if inputs.readiness_score is not None:
        components["readiness"] = inputs.readiness_score
        counts["readiness"] = 1
    if inputs.coverage_subscore is not None:
        components["coverage"] = inputs.coverage_subscore
        counts["coverage"] = 1
    if inputs.confidence_subscore is not None:
        components["confidence"] = inputs.confidence_subscore
        counts["confidence"] = 1

    if not components:
        return None

    weights = redistribute_weights(base_weights, counts)
    raw = weighted_blend(components, weights)
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))


def compute_score_uncertainty(confidence_subscore: Decimal | None) -> Decimal:
    confidence = confidence_subscore if confidence_subscore is not None else Decimal("0")
    return max(_MIN_UNCERTAINTY, (Decimal("100") - confidence) * _UNCERTAINTY_FACTOR)


def compute_predicted_score_range(
    *,
    predicted_score: Decimal,
    confidence_subscore: Decimal | None,
) -> PredictedScoreRange:
    uncertainty = round_score(compute_score_uncertainty(confidence_subscore))
    low = round_score(clamp(predicted_score - uncertainty, Decimal("0"), Decimal("100")))
    high = round_score(clamp(predicted_score + uncertainty, Decimal("0"), Decimal("100")))
    return PredictedScoreRange(
        low_score=low,
        expected_score=predicted_score,
        high_score=high,
    )


def classify_preparation_risk(readiness_score: Decimal | None) -> PreparationRisk:
    if readiness_score is None:
        return PreparationRisk.HIGH
    if readiness_score >= Decimal("80"):
        return PreparationRisk.LOW
    if readiness_score >= Decimal("60"):
        return PreparationRisk.MEDIUM
    return PreparationRisk.HIGH
