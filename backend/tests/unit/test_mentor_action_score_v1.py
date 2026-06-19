from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.mentor.mentor_action_score_v1 import compute_mentor_action_priority_score_v1
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


def test_priority_score_uses_weighted_formula() -> None:
    inputs = _inputs()
    score = compute_mentor_action_priority_score_v1(inputs)
    risk_factor = Decimal("45")
    milestone_factor = Decimal("25")
    revision_factor = Decimal("60")
    effectiveness_factor = Decimal("55")
    expected = Decimal("43.00")
    assert score == expected


def test_priority_score_clamped_to_100() -> None:
    inputs = _inputs(
        forecast=ForecastSignals(
            goal_probability=Decimal("0"),
            gap_to_goal=Decimal("30"),
            on_track=False,
        ),
        milestones=MilestoneSignals(
            milestone_status=MilestoneStatus.BEHIND.value,
            current_gap=Decimal("30"),
        ),
        due_revision_count=20,
        intervention_effectiveness=InterventionEffectivenessSignals(
            last_effectiveness_score=Decimal("100"),
            historical_effectiveness=Decimal("100"),
            outcome_status="EFFECTIVE",
        ),
    )
    score = compute_mentor_action_priority_score_v1(inputs)
    assert score == Decimal("100.00")
