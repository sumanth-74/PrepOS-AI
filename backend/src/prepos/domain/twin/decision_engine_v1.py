from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.scoring.common import clamp, round_score
from prepos.domain.scoring.decision_impact_v1 import (
    DecisionImpactInputs,
    compute_decision_impact_v1,
)
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile
from prepos.domain.twin.decision_explanations_v1 import explain_twin_decision_v1
from prepos.domain.twin.decision_types_v1 import TwinDecisionType

_DUE_REVISION_THRESHOLD = 0
_COVERAGE_RECOVERY_THRESHOLD = Decimal("60")
_GOAL_PROBABILITY_INCREASE_THRESHOLD = Decimal("60")
_GOAL_PROBABILITY_REDUCE_THRESHOLD = Decimal("90")
_COMPLETION_RATE_REDUCE_THRESHOLD = Decimal("0.85")

_DECISION_BASE_SCORE: dict[str, Decimal] = {
    "GOAL_RECOVERY_MODE": Decimal("40"),
    "REVISE_NOW": Decimal("42"),
    "RECOVER_COVERAGE": Decimal("38"),
    "FOCUS_WEAKNESS": Decimal("36"),
    "INCREASE_DAILY_CAPACITY": Decimal("35"),
    "REDUCE_DAILY_CAPACITY": Decimal("30"),
    "MAINTAIN_PLAN": Decimal("25"),
}


@dataclass(frozen=True, slots=True)
class TwinDecisionInputs:
    due_revision_count: int
    high_risk_concept_count: int
    coverage_subscore: Decimal | None
    completion_rate: Decimal
    goal_probability: Decimal | None
    milestone_status: MilestoneStatus | None
    retention_subscore: Decimal | None
    total_estimated_gain: Decimal
    required_gain: Decimal | None
    learning_style: LearningStyle | None = None
    risk_profile: RiskProfile | None = None


@dataclass(frozen=True, slots=True)
class TwinDecision:
    decision_type: TwinDecisionType
    decision_score: Decimal
    explanation: str
    expected_readiness_gain: Decimal
    expected_score_gain: Decimal


def _compute_decision_score(
    *,
    decision_type: TwinDecisionType,
    expected_readiness_gain: Decimal,
    expected_score_gain: Decimal,
) -> Decimal:
    base = _DECISION_BASE_SCORE[decision_type.value]
    raw = (
        base
        + expected_readiness_gain * Decimal("10")
        + expected_score_gain * Decimal("5")
    )
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))


_BEHAVIOR_DECISION_BOOST = Decimal("10")


def _behavior_decision_boost(
    *,
    decision_type: TwinDecisionType,
    learning_style: LearningStyle | None,
    risk_profile: RiskProfile | None,
) -> Decimal:
    if risk_profile == RiskProfile.HIGH_RISK and decision_type == TwinDecisionType.GOAL_RECOVERY_MODE:
        return _BEHAVIOR_DECISION_BOOST
    if (
        learning_style == LearningStyle.RECOVERY_DRIVEN
        and decision_type == TwinDecisionType.FOCUS_WEAKNESS
    ):
        return _BEHAVIOR_DECISION_BOOST
    if (
        learning_style == LearningStyle.CONSISTENT_LEARNER
        and decision_type == TwinDecisionType.MAINTAIN_PLAN
    ):
        return _BEHAVIOR_DECISION_BOOST
    return Decimal("0")


def select_twin_decision_v1(inputs: TwinDecisionInputs) -> TwinDecision:
    """Deterministic priority-based decision selection."""
    if inputs.milestone_status == MilestoneStatus.BEHIND:
        decision_type = TwinDecisionType.GOAL_RECOVERY_MODE
    elif inputs.due_revision_count > _DUE_REVISION_THRESHOLD:
        decision_type = TwinDecisionType.REVISE_NOW
    elif inputs.coverage_subscore is not None and inputs.coverage_subscore < _COVERAGE_RECOVERY_THRESHOLD:
        decision_type = TwinDecisionType.RECOVER_COVERAGE
    elif (
        inputs.high_risk_concept_count > 0
        and inputs.high_risk_concept_count >= max(inputs.due_revision_count, 1)
    ):
        decision_type = TwinDecisionType.FOCUS_WEAKNESS
    elif (
        inputs.goal_probability is not None
        and inputs.goal_probability < _GOAL_PROBABILITY_INCREASE_THRESHOLD
    ):
        decision_type = TwinDecisionType.INCREASE_DAILY_CAPACITY
    elif (
        inputs.goal_probability is not None
        and inputs.goal_probability > _GOAL_PROBABILITY_REDUCE_THRESHOLD
        and inputs.completion_rate > _COMPLETION_RATE_REDUCE_THRESHOLD
    ):
        decision_type = TwinDecisionType.REDUCE_DAILY_CAPACITY
    else:
        decision_type = TwinDecisionType.MAINTAIN_PLAN

    impact = compute_decision_impact_v1(
        decision_type=decision_type.value,
        inputs=DecisionImpactInputs(
            due_revision_count=inputs.due_revision_count,
            high_risk_concept_count=inputs.high_risk_concept_count,
            coverage_subscore=inputs.coverage_subscore,
            retention_subscore=inputs.retention_subscore,
            total_estimated_gain=inputs.total_estimated_gain,
            required_gain=inputs.required_gain,
            goal_probability=inputs.goal_probability,
        ),
    )
    decision_score = _compute_decision_score(
        decision_type=decision_type,
        expected_readiness_gain=impact.expected_readiness_gain,
        expected_score_gain=impact.expected_score_gain,
    )
    behavior_boost = _behavior_decision_boost(
        decision_type=decision_type,
        learning_style=inputs.learning_style,
        risk_profile=inputs.risk_profile,
    )
    if behavior_boost > Decimal("0"):
        decision_score = round_score(
            clamp(decision_score + behavior_boost, Decimal("0"), Decimal("100"))
        )
    explanation = explain_twin_decision_v1(
        decision_type=decision_type,
        expected_readiness_gain=impact.expected_readiness_gain,
        milestone_status=inputs.milestone_status,
        due_revision_count=inputs.due_revision_count,
    )
    return TwinDecision(
        decision_type=decision_type,
        decision_score=decision_score,
        explanation=explanation,
        expected_readiness_gain=impact.expected_readiness_gain,
        expected_score_gain=impact.expected_score_gain,
    )
