from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile
from prepos.domain.twin.decision_engine_v1 import TwinDecision
from prepos.domain.twin.decision_types_v1 import TwinDecisionType
from prepos.domain.twin.interventions_v1 import TwinInterventionInputs, build_twin_intervention_v1
from prepos.domain.twin.personalized_scoring_v1 import PersonalizationContext


def _decision(decision_type: TwinDecisionType) -> TwinDecision:
    return TwinDecision(
        decision_type=decision_type,
        decision_score=Decimal("50"),
        explanation="test",
        expected_readiness_gain=Decimal("3"),
        expected_score_gain=Decimal("2"),
    )


def test_personalized_intervention_score_uses_history_and_style() -> None:
    baseline = build_twin_intervention_v1(
        TwinInterventionInputs(
            decision=_decision(TwinDecisionType.FOCUS_WEAKNESS),
            goal_probability=Decimal("75"),
            milestone_status=MilestoneStatus.ON_TRACK,
            due_revision_count=0,
            daily_plan_count=3,
        )
    )
    personalized = build_twin_intervention_v1(
        TwinInterventionInputs(
            decision=_decision(TwinDecisionType.FOCUS_WEAKNESS),
            goal_probability=Decimal("75"),
            milestone_status=MilestoneStatus.ON_TRACK,
            due_revision_count=0,
            daily_plan_count=3,
            personalization=PersonalizationContext(
                learning_style=LearningStyle.RECOVERY_DRIVEN,
                risk_profile=RiskProfile.MEDIUM_RISK,
                effectiveness_by_activity={
                    ActivityType.WEAKNESS_RECOVERY.value: Decimal("60"),
                },
            ),
        )
    )
    assert personalized.intervention_score > baseline.intervention_score
