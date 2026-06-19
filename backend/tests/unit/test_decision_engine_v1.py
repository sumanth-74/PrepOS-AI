from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.twin.decision_engine_v1 import TwinDecisionInputs, select_twin_decision_v1
from prepos.domain.twin.decision_types_v1 import TwinDecisionType


def test_goal_recovery_mode_when_milestone_behind() -> None:
    decision = select_twin_decision_v1(
        TwinDecisionInputs(
            due_revision_count=0,
            high_risk_concept_count=0,
            coverage_subscore=Decimal("80"),
            completion_rate=Decimal("0.90"),
            goal_probability=Decimal("75"),
            milestone_status=MilestoneStatus.BEHIND,
            retention_subscore=Decimal("70"),
            total_estimated_gain=Decimal("5"),
            required_gain=Decimal("10"),
        )
    )
    assert decision.decision_type == TwinDecisionType.GOAL_RECOVERY_MODE


def test_revise_now_when_due_revisions_present() -> None:
    decision = select_twin_decision_v1(
        TwinDecisionInputs(
            due_revision_count=3,
            high_risk_concept_count=1,
            coverage_subscore=Decimal("80"),
            completion_rate=Decimal("0.70"),
            goal_probability=Decimal("75"),
            milestone_status=MilestoneStatus.ON_TRACK,
            retention_subscore=Decimal("55"),
            total_estimated_gain=Decimal("5"),
            required_gain=Decimal("10"),
        )
    )
    assert decision.decision_type == TwinDecisionType.REVISE_NOW
    assert decision.explanation == (
        "Completing overdue revisions is currently the fastest path to improve readiness."
    )


def test_recover_coverage_when_below_threshold() -> None:
    decision = select_twin_decision_v1(
        TwinDecisionInputs(
            due_revision_count=0,
            high_risk_concept_count=0,
            coverage_subscore=Decimal("45"),
            completion_rate=Decimal("0.70"),
            goal_probability=Decimal("75"),
            milestone_status=MilestoneStatus.ON_TRACK,
            retention_subscore=Decimal("70"),
            total_estimated_gain=Decimal("5"),
            required_gain=Decimal("10"),
        )
    )
    assert decision.decision_type == TwinDecisionType.RECOVER_COVERAGE


def test_increase_daily_capacity_when_goal_probability_low() -> None:
    decision = select_twin_decision_v1(
        TwinDecisionInputs(
            due_revision_count=0,
            high_risk_concept_count=0,
            coverage_subscore=Decimal("70"),
            completion_rate=Decimal("0.70"),
            goal_probability=Decimal("55"),
            milestone_status=MilestoneStatus.ON_TRACK,
            retention_subscore=Decimal("70"),
            total_estimated_gain=Decimal("8"),
            required_gain=Decimal("12"),
        )
    )
    assert decision.decision_type == TwinDecisionType.INCREASE_DAILY_CAPACITY


def test_reduce_daily_capacity_when_probability_high_and_completion_strong() -> None:
    decision = select_twin_decision_v1(
        TwinDecisionInputs(
            due_revision_count=0,
            high_risk_concept_count=0,
            coverage_subscore=Decimal("70"),
            completion_rate=Decimal("0.90"),
            goal_probability=Decimal("92"),
            milestone_status=MilestoneStatus.ON_TRACK,
            retention_subscore=Decimal("70"),
            total_estimated_gain=Decimal("2"),
            required_gain=Decimal("2"),
        )
    )
    assert decision.decision_type == TwinDecisionType.REDUCE_DAILY_CAPACITY


def test_maintain_plan_is_default() -> None:
    decision = select_twin_decision_v1(
        TwinDecisionInputs(
            due_revision_count=0,
            high_risk_concept_count=0,
            coverage_subscore=Decimal("70"),
            completion_rate=Decimal("0.75"),
            goal_probability=Decimal("72"),
            milestone_status=MilestoneStatus.ON_TRACK,
            retention_subscore=Decimal("70"),
            total_estimated_gain=Decimal("3"),
            required_gain=Decimal("5"),
        )
    )
    assert decision.decision_type == TwinDecisionType.MAINTAIN_PLAN


def test_decision_score_uses_impact_components() -> None:
    decision = select_twin_decision_v1(
        TwinDecisionInputs(
            due_revision_count=2,
            high_risk_concept_count=0,
            coverage_subscore=Decimal("80"),
            completion_rate=Decimal("0.70"),
            goal_probability=Decimal("75"),
            milestone_status=MilestoneStatus.ON_TRACK,
            retention_subscore=Decimal("55"),
            total_estimated_gain=Decimal("5"),
            required_gain=Decimal("10"),
        )
    )
    assert decision.decision_type == TwinDecisionType.REVISE_NOW
    assert decision.expected_readiness_gain > Decimal("0")
    assert decision.expected_score_gain > Decimal("0")
    assert decision.decision_score > Decimal("60")
