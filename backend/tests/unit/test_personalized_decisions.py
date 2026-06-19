from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile
from prepos.domain.twin.decision_engine_v1 import TwinDecisionInputs, select_twin_decision_v1
from prepos.domain.twin.decision_types_v1 import TwinDecisionType


def _inputs(**overrides: object) -> TwinDecisionInputs:
    base = {
        "due_revision_count": 0,
        "high_risk_concept_count": 0,
        "coverage_subscore": Decimal("80"),
        "completion_rate": Decimal("0.80"),
        "goal_probability": Decimal("80"),
        "milestone_status": MilestoneStatus.ON_TRACK,
        "retention_subscore": Decimal("70"),
        "total_estimated_gain": Decimal("5"),
        "required_gain": Decimal("10"),
        "learning_style": None,
        "risk_profile": None,
    }
    base.update(overrides)
    return TwinDecisionInputs(**base)  # type: ignore[arg-type]


def test_high_risk_boosts_goal_recovery_mode_score() -> None:
    baseline = select_twin_decision_v1(
        _inputs(
            milestone_status=MilestoneStatus.BEHIND,
            risk_profile=None,
        )
    )
    boosted = select_twin_decision_v1(
        _inputs(
            milestone_status=MilestoneStatus.BEHIND,
            risk_profile=RiskProfile.HIGH_RISK,
        )
    )
    assert baseline.decision_type == TwinDecisionType.GOAL_RECOVERY_MODE
    assert boosted.decision_score == baseline.decision_score + Decimal("10")


def test_recovery_driven_boosts_focus_weakness_score() -> None:
    baseline = select_twin_decision_v1(
        _inputs(
            high_risk_concept_count=3,
            due_revision_count=0,
            goal_probability=Decimal("75"),
        )
    )
    boosted = select_twin_decision_v1(
        _inputs(
            high_risk_concept_count=3,
            due_revision_count=0,
            goal_probability=Decimal("75"),
            learning_style=LearningStyle.RECOVERY_DRIVEN,
        )
    )
    assert baseline.decision_type == TwinDecisionType.FOCUS_WEAKNESS
    assert boosted.decision_score > baseline.decision_score


def test_consistent_learner_boosts_maintain_plan_score() -> None:
    baseline = select_twin_decision_v1(_inputs())
    boosted = select_twin_decision_v1(
        _inputs(learning_style=LearningStyle.CONSISTENT_LEARNER)
    )
    assert baseline.decision_type == TwinDecisionType.MAINTAIN_PLAN
    assert boosted.decision_score == baseline.decision_score + Decimal("10")
