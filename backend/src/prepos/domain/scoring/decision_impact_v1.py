from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score
from prepos.domain.scoring.exam_simulation_v1 import compute_retention_decay_penalty

DECISION_IMPACT_V1 = "decision_impact_v1"

_SCORE_GAIN_FACTOR = Decimal("0.70")
_CAPACITY_GAIN_FACTOR = Decimal("0.15")
_COVERAGE_GAIN_FACTOR = Decimal("0.20")
_COVERAGE_RECOVERY_THRESHOLD = Decimal("60")
_WEAKNESS_GAIN_FACTOR = Decimal("1.50")


@dataclass(frozen=True, slots=True)
class DecisionImpactInputs:
    due_revision_count: int
    high_risk_concept_count: int
    coverage_subscore: Decimal | None
    retention_subscore: Decimal | None
    total_estimated_gain: Decimal
    required_gain: Decimal | None
    goal_probability: Decimal | None


@dataclass(frozen=True, slots=True)
class DecisionImpactResult:
    expected_readiness_gain: Decimal
    expected_score_gain: Decimal


def _score_gain(readiness_gain: Decimal) -> Decimal:
    return round_score(readiness_gain * _SCORE_GAIN_FACTOR)


def compute_decision_impact_v1(
    *,
    decision_type: str,
    inputs: DecisionImpactInputs,
) -> DecisionImpactResult:
    """Deterministic expected impact models per decision type."""
    if decision_type == "REVISE_NOW":
        penalty = compute_retention_decay_penalty(inputs.retention_subscore)
        per_revision = penalty / Decimal("2")
        readiness_gain = round_score(
            clamp(
                Decimal(inputs.due_revision_count) * per_revision,
                Decimal("0"),
                Decimal("10"),
            )
        )
    elif decision_type == "FOCUS_WEAKNESS":
        readiness_gain = round_score(
            clamp(
                Decimal(inputs.high_risk_concept_count) * _WEAKNESS_GAIN_FACTOR,
                Decimal("0"),
                Decimal("8"),
            )
        )
    elif decision_type == "INCREASE_DAILY_CAPACITY":
        gap = inputs.required_gain if inputs.required_gain is not None else Decimal("0")
        readiness_gain = round_score(
            clamp(gap * _CAPACITY_GAIN_FACTOR + inputs.total_estimated_gain, Decimal("0"), Decimal("12"))
        )
    elif decision_type == "GOAL_RECOVERY_MODE":
        gap = inputs.required_gain if inputs.required_gain is not None else Decimal("5")
        readiness_gain = round_score(clamp(gap * Decimal("0.25"), Decimal("2"), Decimal("10")))
    elif decision_type == "RECOVER_COVERAGE":
        coverage = inputs.coverage_subscore if inputs.coverage_subscore is not None else Decimal("0")
        gap = max(_COVERAGE_RECOVERY_THRESHOLD - coverage, Decimal("0"))
        readiness_gain = round_score(clamp(gap * _COVERAGE_GAIN_FACTOR, Decimal("0"), Decimal("8")))
    elif decision_type == "REDUCE_DAILY_CAPACITY":
        readiness_gain = Decimal("0.50")
    else:
        readiness_gain = round_score(
            clamp(inputs.total_estimated_gain * Decimal("0.10"), Decimal("0"), Decimal("3"))
        )

    return DecisionImpactResult(
        expected_readiness_gain=readiness_gain,
        expected_score_gain=_score_gain(readiness_gain),
    )
