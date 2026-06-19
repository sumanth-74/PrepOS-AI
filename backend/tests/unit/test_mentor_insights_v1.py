from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
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
    classify_insight_priority,
    generate_mentor_insights_v1,
)
from prepos.domain.mentor.mentor_types_v1 import InsightPriority, InsightType
from prepos.domain.twin.behavior_profile_types_v1 import RiskProfile


def _inputs(**overrides: object) -> MentorInsightInputs:
    base = {
        "readiness": ReadinessSignals(
            readiness_score=Decimal("70"),
            coverage_subscore=Decimal("55"),
            largest_negative_driver="coverage",
        ),
        "forecast": ForecastSignals(
            goal_probability=Decimal("55"),
            gap_to_goal=Decimal("10"),
            on_track=False,
        ),
        "milestones": MilestoneSignals(
            milestone_status=MilestoneStatus.ON_TRACK.value,
            current_gap=Decimal("5"),
        ),
        "intervention_effectiveness": InterventionEffectivenessSignals(
            last_effectiveness_score=Decimal("60"),
            historical_effectiveness=Decimal("55"),
            outcome_status="EFFECTIVE",
        ),
        "behavior_profile": BehaviorProfileSignals(
            consistency_score=Decimal("85"),
            discipline_score=Decimal("70"),
            risk_profile=RiskProfile.MEDIUM_RISK.value,
            learning_style="CONSISTENT_LEARNER",
        ),
        "personalization": PersonalizationSignals(
            best_activity_type="WEAKNESS_RECOVERY",
            top_multiplier=Decimal("1.30"),
            historical_effectiveness=Decimal("72"),
        ),
        "study_plan": StudyPlanSignals(
            total_estimated_gain=Decimal("8"),
            daily_item_count=4,
            completion_rate=Decimal("0.80"),
        ),
        "optimization": OptimizationSignals(
            best_intervention="WEAKNESS_REMEDIATION",
            historical_effectiveness=Decimal("60"),
            optimized_intervention_score=Decimal("75"),
        ),
        "due_revision_count": 6,
        "high_risk_concept_count": 2,
    }
    base.update(overrides)
    return MentorInsightInputs(**base)  # type: ignore[arg-type]


def test_generates_goal_risk_and_revision_warning() -> None:
    insights = generate_mentor_insights_v1(_inputs())
    insight_types = {item.insight_type for item in insights}
    assert InsightType.GOAL_RISK in insight_types
    assert InsightType.REVISION_WARNING in insight_types
    assert InsightType.POSITIVE_PROGRESS in insight_types


def test_critical_priority_for_low_goal_probability() -> None:
    priority = classify_insight_priority(
        insight_type=InsightType.GOAL_RISK,
        goal_probability=Decimal("35"),
        milestone_status=MilestoneStatus.ON_TRACK.value,
        due_revision_count=0,
        risk_profile=RiskProfile.LOW_RISK.value,
    )
    assert priority == InsightPriority.CRITICAL


def test_milestone_alert_when_behind() -> None:
    insights = generate_mentor_insights_v1(
        _inputs(
            milestones=MilestoneSignals(
                milestone_status=MilestoneStatus.BEHIND.value,
                current_gap=Decimal("12"),
            )
        )
    )
    milestone_insights = [item for item in insights if item.insight_type == InsightType.MILESTONE_ALERT]
    assert milestone_insights
    assert milestone_insights[0].priority == InsightPriority.CRITICAL
