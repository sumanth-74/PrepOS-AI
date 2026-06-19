from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, redistribute_weights, round_score, shrink, weighted_blend
from prepos.domain.scoring.config import DEFAULT_SCORING_CONFIG, ScoringConfig

CONFIDENCE_V1 = "confidence_v1"


@dataclass(frozen=True, slots=True)
class ConfidenceInputs:
    """Deterministic confidence inputs (Assessment §16 + Learning Graph §8.4)."""

    n_mcq: int
    mcq_accuracy_unit: Decimal
    self_confidence: Decimal | None = None
    speed_score: Decimal | None = None
    self_assessment_values: tuple[Decimal, ...] = ()


@dataclass(frozen=True, slots=True)
class ConfidenceResult:
    value: Decimal
    version: str
    raw_unit: Decimal
    shrunk_unit: Decimal
    n_evidence: int
    active_signals: tuple[str, ...]
    redistributed_weights: dict[str, Decimal]


def map_self_assessment(scale_1_to_5: Decimal) -> Decimal:
    """Map a 1–5 self-assessment scale to 0–100."""
    clamped = clamp(scale_1_to_5, Decimal("1"), Decimal("5"))
    return (clamped - Decimal("1")) / Decimal("4") * Decimal("100")


def compute_speed_score(response_time_sec: Decimal, cohort_median_sec: Decimal) -> Decimal:
    """Normalize response speed vs cohort median (Assessment §16.2)."""
    if cohort_median_sec <= 0:
        return Decimal("0")
    ratio = response_time_sec / cohort_median_sec
    return clamp((Decimal("1") - ratio) * Decimal("100"), Decimal("0"), Decimal("100"))


def compute_consistency_score(self_assessment_values: tuple[Decimal, ...]) -> Decimal:
    """Higher score when self-assessments are stable across attempts (Assessment §16)."""
    if len(self_assessment_values) < 2:
        return Decimal("50")

    mean_value = sum(self_assessment_values, start=Decimal("0")) / Decimal(len(self_assessment_values))
    variance = sum((value - mean_value) ** 2 for value in self_assessment_values) / Decimal(
        len(self_assessment_values)
    )
    max_variance = Decimal("2500")
    normalized_variance = clamp(variance / max_variance, Decimal("0"), Decimal("1"))
    return clamp(Decimal("100") * (Decimal("1") - normalized_variance), Decimal("0"), Decimal("100"))


def compute_confidence_v1(
    inputs: ConfidenceInputs,
    *,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> ConfidenceResult:
    """Deterministic confidence from MCQ accuracy and optional self-report signals."""
    signal_values: dict[str, Decimal] = {}
    signal_counts: dict[str, int] = {}
    base_weights = {
        "self": config.CONF_W_SELF,
        "speed": config.CONF_W_SPEED,
        "consistency": config.CONF_W_CONSISTENCY,
    }

    if inputs.self_confidence is not None:
        signal_values["self"] = clamp(inputs.self_confidence, Decimal("0"), Decimal("100")) / Decimal("100")
        signal_counts["self"] = 1
    elif inputs.n_mcq > 0:
        signal_values["self"] = clamp(inputs.mcq_accuracy_unit, Decimal("0"), Decimal("1"))
        signal_counts["self"] = inputs.n_mcq

    if inputs.speed_score is not None:
        signal_values["speed"] = clamp(inputs.speed_score, Decimal("0"), Decimal("100")) / Decimal("100")
        signal_counts["speed"] = max(inputs.n_mcq, 1)

    if inputs.self_assessment_values:
        consistency = compute_consistency_score(inputs.self_assessment_values)
        signal_values["consistency"] = consistency / Decimal("100")
        signal_counts["consistency"] = len(inputs.self_assessment_values)
    elif inputs.n_mcq > 0:
        signal_values["consistency"] = clamp(inputs.mcq_accuracy_unit, Decimal("0"), Decimal("1"))
        signal_counts["consistency"] = inputs.n_mcq

    redistributed = redistribute_weights(base_weights, signal_counts)
    n_evidence = inputs.n_mcq + len(inputs.self_assessment_values)

    if not redistributed:
        prior_unit = config.CONF_PRIOR / Decimal("100")
        return ConfidenceResult(
            value=Decimal("0"),
            version=CONFIDENCE_V1,
            raw_unit=Decimal("0"),
            shrunk_unit=prior_unit,
            n_evidence=0,
            active_signals=(),
            redistributed_weights={},
        )

    raw_unit = weighted_blend(signal_values, redistributed)
    prior_unit = config.CONF_PRIOR / Decimal("100")
    shrunk_unit = shrink(raw_unit, n_evidence, config.CONF_K_CONF, prior_unit)
    value = round_score(Decimal("100") * shrunk_unit)

    return ConfidenceResult(
        value=value,
        version=CONFIDENCE_V1,
        raw_unit=raw_unit,
        shrunk_unit=shrunk_unit,
        n_evidence=n_evidence,
        active_signals=tuple(redistributed),
        redistributed_weights=redistributed,
    )
