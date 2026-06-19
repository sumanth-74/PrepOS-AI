from __future__ import annotations

from decimal import Decimal

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
from prepos.domain.mentor.mentor_summary_v1 import build_mentor_summary_v1, classify_overall_status
from prepos.domain.mentor.mentor_types_v1 import OverallStatus


def test_classify_excellent_status() -> None:
    status = classify_overall_status(
        readiness_score=Decimal("85"),
        goal_probability=Decimal("85"),
    )
    assert status == OverallStatus.EXCELLENT


def test_classify_critical_status() -> None:
    status = classify_overall_status(
        readiness_score=Decimal("70"),
        goal_probability=Decimal("35"),
    )
    assert status == OverallStatus.CRITICAL


def test_build_summary_uses_top_insight_message() -> None:
    from prepos.domain.mentor.mentor_insights_v1 import generate_mentor_insights_v1

    inputs = MentorInsightInputs(
        readiness=ReadinessSignals(
            readiness_score=Decimal("55"),
            coverage_subscore=Decimal("45"),
            largest_negative_driver="coverage",
        ),
        forecast=ForecastSignals(
            goal_probability=Decimal("55"),
            gap_to_goal=Decimal("12"),
            on_track=False,
        ),
        milestones=MilestoneSignals(milestone_status="ON_TRACK", current_gap=Decimal("5")),
        intervention_effectiveness=InterventionEffectivenessSignals(None, None, None),
        behavior_profile=BehaviorProfileSignals(None, None, "MEDIUM_RISK", None),
        personalization=PersonalizationSignals(None, None, None),
        study_plan=StudyPlanSignals(Decimal("5"), 3, Decimal("0.7")),
        optimization=OptimizationSignals(None, None, None),
        due_revision_count=6,
    )
    insights = generate_mentor_insights_v1(inputs)
    summary = build_mentor_summary_v1(inputs=inputs, insights=insights)
    assert summary.overall_status == OverallStatus.AT_RISK
    assert summary.key_message == insights[0].message
    assert summary.weakest_signal in {"coverage", "revision_backlog", "goal_probability"}
