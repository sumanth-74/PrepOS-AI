from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.twin.decision_engine_v1 import TwinDecision
from prepos.domain.twin.decision_types_v1 import TwinDecisionType
from prepos.domain.twin.intervention_types_v1 import InterventionUrgency, TwinInterventionType
from prepos.domain.twin.interventions_v1 import (
    TwinInterventionInputs,
    build_twin_intervention_v1,
    classify_intervention_urgency,
    map_decision_to_intervention,
)


def _decision(
    decision_type: TwinDecisionType,
    *,
    score: Decimal = Decimal("80"),
    readiness_gain: Decimal = Decimal("3.2"),
) -> TwinDecision:
    return TwinDecision(
        decision_type=decision_type,
        decision_score=score,
        explanation="test",
        expected_readiness_gain=readiness_gain,
        expected_score_gain=Decimal("2.1"),
    )


def test_map_revise_now_to_revision_sprint() -> None:
    assert map_decision_to_intervention(TwinDecisionType.REVISE_NOW) == TwinInterventionType.REVISION_SPRINT


def test_map_focus_weakness_to_weakness_remediation() -> None:
    assert (
        map_decision_to_intervention(TwinDecisionType.FOCUS_WEAKNESS)
        == TwinInterventionType.WEAKNESS_REMEDIATION
    )


def test_map_goal_recovery_mode_to_capacity_increase() -> None:
    assert (
        map_decision_to_intervention(TwinDecisionType.GOAL_RECOVERY_MODE)
        == TwinInterventionType.CAPACITY_INCREASE
    )


def test_urgency_critical_when_goal_probability_below_40() -> None:
    urgency = classify_intervention_urgency(
        goal_probability=Decimal("35"),
        milestone_status=MilestoneStatus.ON_TRACK,
        due_revision_count=0,
        decision_type=TwinDecisionType.MAINTAIN_PLAN,
    )
    assert urgency == InterventionUrgency.CRITICAL


def test_urgency_high_when_milestone_behind() -> None:
    urgency = classify_intervention_urgency(
        goal_probability=Decimal("75"),
        milestone_status=MilestoneStatus.BEHIND,
        due_revision_count=0,
        decision_type=TwinDecisionType.GOAL_RECOVERY_MODE,
    )
    assert urgency == InterventionUrgency.HIGH


def test_urgency_high_when_due_revisions_present() -> None:
    urgency = classify_intervention_urgency(
        goal_probability=Decimal("75"),
        milestone_status=MilestoneStatus.ON_TRACK,
        due_revision_count=2,
        decision_type=TwinDecisionType.REVISE_NOW,
    )
    assert urgency == InterventionUrgency.HIGH


def test_urgency_low_when_maintaining_on_track_goal() -> None:
    urgency = classify_intervention_urgency(
        goal_probability=Decimal("85"),
        milestone_status=MilestoneStatus.ON_TRACK,
        due_revision_count=0,
        decision_type=TwinDecisionType.MAINTAIN_PLAN,
    )
    assert urgency == InterventionUrgency.LOW


def test_build_intervention_for_revision_sprint() -> None:
    intervention = build_twin_intervention_v1(
        TwinInterventionInputs(
            decision=_decision(TwinDecisionType.REVISE_NOW),
            goal_probability=Decimal("75"),
            milestone_status=MilestoneStatus.ON_TRACK,
            due_revision_count=3,
            daily_plan_count=5,
        )
    )
    assert intervention.intervention_type == TwinInterventionType.REVISION_SPRINT
    assert intervention.urgency == InterventionUrgency.HIGH
    assert "3" in intervention.title
    assert intervention.intervention_score > Decimal("0")
