from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.mentor.coaching_recommendations_v1 import generate_coaching_recommendations_v1
from prepos.domain.mentor.mentor_insights_v1 import (
    BehaviorProfileSignals,
    ForecastSignals,
    InterventionEffectivenessSignals,
    MentorInsightInputs,
    MilestoneSignals,
    OptimizationSignals,
    PersonalizationSignals,
    ReadinessSignals,
    StudyPlanSignals,
)
from prepos.domain.mentor.mentor_types_v1 import CoachingAction


def test_recommends_complete_revisions_when_backlog_high() -> None:
    recommendations = generate_coaching_recommendations_v1(
        MentorInsightInputs(
            readiness=ReadinessSignals(Decimal("70"), Decimal("60"), "retention"),
            forecast=ForecastSignals(Decimal("75"), Decimal("5"), True),
            milestones=MilestoneSignals(MilestoneStatus.ON_TRACK.value, Decimal("3")),
            intervention_effectiveness=InterventionEffectivenessSignals(None, None, None),
            behavior_profile=BehaviorProfileSignals(None, None, None, None),
            personalization=PersonalizationSignals(None, None, None),
            study_plan=StudyPlanSignals(Decimal("6"), 4, Decimal("0.8")),
            optimization=OptimizationSignals(None, None, None),
            due_revision_count=8,
        )
    )
    assert recommendations[0].action == CoachingAction.COMPLETE_REVISIONS


def test_maintain_plan_when_no_risk_signals() -> None:
    recommendations = generate_coaching_recommendations_v1(
        MentorInsightInputs(
            readiness=ReadinessSignals(Decimal("75"), Decimal("70"), None),
            forecast=ForecastSignals(Decimal("85"), Decimal("2"), True),
            milestones=MilestoneSignals(MilestoneStatus.ON_TRACK.value, Decimal("1")),
            intervention_effectiveness=InterventionEffectivenessSignals(None, None, None),
            behavior_profile=BehaviorProfileSignals(Decimal("80"), None, "LOW_RISK", None),
            personalization=PersonalizationSignals("REVISION", Decimal("1.05"), Decimal("40")),
            study_plan=StudyPlanSignals(Decimal("4"), 3, Decimal("0.9")),
            optimization=OptimizationSignals("REVISION_SPRINT", Decimal("45"), Decimal("60")),
            due_revision_count=0,
            high_risk_concept_count=0,
        )
    )
    assert any(item.action == CoachingAction.MAINTAIN_CURRENT_PLAN for item in recommendations)
