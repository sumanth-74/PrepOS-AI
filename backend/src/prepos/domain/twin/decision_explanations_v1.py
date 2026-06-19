from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.scoring.common import round_score
from prepos.domain.twin.decision_types_v1 import TwinDecisionType

DECISION_EXPLANATIONS_V1 = "decision_explanations_v1"


def _format_gain(value: Decimal) -> str:
    return f"{round_score(value):.2f}".rstrip("0").rstrip(".")


def explain_twin_decision_v1(
    *,
    decision_type: TwinDecisionType,
    expected_readiness_gain: Decimal,
    milestone_status: MilestoneStatus | None,
    due_revision_count: int,
) -> str:
    """Deterministic rule-based decision explanations."""
    if decision_type == TwinDecisionType.GOAL_RECOVERY_MODE:
        return (
            "You are behind your milestone trajectory; prioritize goal recovery actions "
            "before adding new topics."
        )
    if decision_type == TwinDecisionType.REVISE_NOW:
        if due_revision_count > 0:
            return (
                "Completing overdue revisions is currently the fastest path to improve readiness."
            )
        return "Revision work should remain your immediate focus to stabilize retention."
    if decision_type == TwinDecisionType.RECOVER_COVERAGE:
        return "Expanding rated concept coverage will unlock more reliable readiness signals."
    if decision_type == TwinDecisionType.FOCUS_WEAKNESS:
        gain = _format_gain(expected_readiness_gain)
        return f"Targeting weak concepts could improve readiness by about {gain} points."
    if decision_type == TwinDecisionType.INCREASE_DAILY_CAPACITY:
        return "Increasing daily study capacity is recommended to raise goal achievement probability."
    if decision_type == TwinDecisionType.REDUCE_DAILY_CAPACITY:
        return "Strong completion rates suggest you can maintain progress with slightly less daily load."
    if milestone_status == MilestoneStatus.AHEAD:
        return "Maintaining your current study plan keeps you ahead of your milestone trajectory."
    return "Maintaining your current study plan keeps you on track."
