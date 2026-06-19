from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.mentor.escalation_v1 import classify_escalation_level_v1
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
from prepos.domain.mentor.mentor_types_v1 import EscalationLevel
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
        "due_revision_count": 2,
        "high_risk_concept_count": 1,
    }
    base.update(overrides)
    return MentorInsightInputs(**base)  # type: ignore[arg-type]


def test_critical_when_goal_probability_below_30() -> None:
    inputs = _inputs(
        forecast=ForecastSignals(
            goal_probability=Decimal("25"),
            gap_to_goal=Decimal("20"),
            on_track=False,
        )
    )
    assert classify_escalation_level_v1(inputs) == EscalationLevel.CRITICAL


def test_high_when_goal_probability_below_50() -> None:
    inputs = _inputs(
        forecast=ForecastSignals(
            goal_probability=Decimal("45"),
            gap_to_goal=Decimal("10"),
            on_track=False,
        )
    )
    assert classify_escalation_level_v1(inputs) == EscalationLevel.HIGH


def test_medium_when_milestone_behind() -> None:
    inputs = _inputs(
        forecast=ForecastSignals(
            goal_probability=Decimal("60"),
            gap_to_goal=Decimal("5"),
            on_track=True,
        ),
        milestones=MilestoneSignals(
            milestone_status=MilestoneStatus.BEHIND.value,
            current_gap=Decimal("8"),
        ),
    )
    assert classify_escalation_level_v1(inputs) == EscalationLevel.MEDIUM


def test_low_when_high_risk_profile() -> None:
    inputs = _inputs(
        forecast=ForecastSignals(
            goal_probability=Decimal("70"),
            gap_to_goal=Decimal("0"),
            on_track=True,
        ),
        behavior_profile=BehaviorProfileSignals(
            consistency_score=Decimal("40"),
            discipline_score=Decimal("35"),
            risk_profile=RiskProfile.HIGH_RISK.value,
            learning_style="INCONSISTENT_LEARNER",
        ),
    )
    assert classify_escalation_level_v1(inputs) == EscalationLevel.LOW


def test_none_when_no_escalation_signals() -> None:
    inputs = _inputs(
        forecast=ForecastSignals(
            goal_probability=Decimal("80"),
            gap_to_goal=Decimal("0"),
            on_track=True,
        )
    )
    assert classify_escalation_level_v1(inputs) == EscalationLevel.NONE
