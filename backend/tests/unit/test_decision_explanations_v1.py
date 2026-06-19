from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.twin.decision_types_v1 import TwinDecisionType
from prepos.domain.twin.decision_explanations_v1 import explain_twin_decision_v1


def test_explanations_are_deterministic() -> None:
    revise = explain_twin_decision_v1(
        decision_type=TwinDecisionType.REVISE_NOW,
        expected_readiness_gain=Decimal("3.2"),
        milestone_status=MilestoneStatus.ON_TRACK,
        due_revision_count=2,
    )
    assert revise == (
        "Completing overdue revisions is currently the fastest path to improve readiness."
    )

    recovery = explain_twin_decision_v1(
        decision_type=TwinDecisionType.GOAL_RECOVERY_MODE,
        expected_readiness_gain=Decimal("2.5"),
        milestone_status=MilestoneStatus.BEHIND,
        due_revision_count=0,
    )
    assert "behind your milestone trajectory" in recovery

    maintain = explain_twin_decision_v1(
        decision_type=TwinDecisionType.MAINTAIN_PLAN,
        expected_readiness_gain=Decimal("0.5"),
        milestone_status=MilestoneStatus.ON_TRACK,
        due_revision_count=0,
    )
    assert maintain == "Maintaining your current study plan keeps you on track."
