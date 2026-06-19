from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.mentor.mentor_actions_v1 import MentorActionInputs, build_mentor_action_v1
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
    generate_mentor_insights_v1,
)
from prepos.domain.mentor.mentor_summary_v1 import build_mentor_summary_v1
from prepos.domain.mentor.mentor_types_v1 import MentorActionType
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


def _action_inputs(inputs: MentorInsightInputs) -> MentorActionInputs:
    insights = generate_mentor_insights_v1(inputs)
    summary = build_mentor_summary_v1(inputs=inputs, insights=insights)
    return MentorActionInputs(summary=summary, insights=insights, signals=inputs)


def test_escalate_risk_when_goal_probability_below_40() -> None:
    inputs = _inputs(
        forecast=ForecastSignals(
            goal_probability=Decimal("35"),
            gap_to_goal=Decimal("20"),
            on_track=False,
        )
    )
    action = build_mentor_action_v1(_action_inputs(inputs))
    assert action.action_type == MentorActionType.ESCALATE_RISK


def test_contact_student_when_high_risk() -> None:
    inputs = _inputs(
        forecast=ForecastSignals(
            goal_probability=Decimal("55"),
            gap_to_goal=Decimal("10"),
            on_track=False,
        ),
        behavior_profile=BehaviorProfileSignals(
            consistency_score=Decimal("40"),
            discipline_score=Decimal("35"),
            risk_profile=RiskProfile.HIGH_RISK.value,
            learning_style="INCONSISTENT_LEARNER",
        ),
    )
    action = build_mentor_action_v1(_action_inputs(inputs))
    assert action.action_type == MentorActionType.CONTACT_STUDENT


def test_schedule_review_when_milestone_behind() -> None:
    inputs = _inputs(
        milestones=MilestoneSignals(
            milestone_status=MilestoneStatus.BEHIND.value,
            current_gap=Decimal("12"),
        )
    )
    action = build_mentor_action_v1(_action_inputs(inputs))
    assert action.action_type == MentorActionType.SCHEDULE_REVIEW


def test_assign_revision_sprint_when_due_revisions_above_threshold() -> None:
    inputs = _inputs(due_revision_count=6)
    action = build_mentor_action_v1(_action_inputs(inputs))
    assert action.action_type == MentorActionType.ASSIGN_REVISION_SPRINT


def test_increase_study_target_when_off_track() -> None:
    inputs = _inputs(
        forecast=ForecastSignals(
            goal_probability=Decimal("65"),
            gap_to_goal=Decimal("8"),
            on_track=False,
        ),
        due_revision_count=2,
    )
    action = build_mentor_action_v1(_action_inputs(inputs))
    assert action.action_type == MentorActionType.INCREASE_STUDY_TARGET


def test_no_action_required_by_default() -> None:
    inputs = _inputs(
        forecast=ForecastSignals(
            goal_probability=Decimal("75"),
            gap_to_goal=Decimal("0"),
            on_track=True,
        ),
        due_revision_count=1,
    )
    action = build_mentor_action_v1(_action_inputs(inputs))
    assert action.action_type == MentorActionType.NO_ACTION_REQUIRED
