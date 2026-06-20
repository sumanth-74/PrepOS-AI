from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.application.copilot.handlers import mentor as mentor_handlers
from prepos.application.copilot.handlers import student as student_handlers
from prepos.application.goal.dto import GoalResponse
from prepos.application.learning_graph.dto import LearningGraphWeaknessesResponse, WeaknessItemResponse
from prepos.application.study_plan.dto import DailyPlanItemResponse, StudyPlanResponse
from prepos.application.twin.dto import TwinRecommendationResponse
from prepos.application.twin.twin_dto import TwinDashboardResponse, TwinGoalSummaryResponse


@pytest.mark.asyncio
async def test_handle_readiness_low_uses_dashboard_drivers() -> None:
    dashboard = TwinDashboardResponse(
        readiness_score=Decimal("42.50"),
        largest_negative_driver="retention_gap",
        due_revision_count=3,
        high_risk_concept_count=2,
        top_negative_drivers=["retention_gap", "low_coverage"],
    )
    answer, sources = await student_handlers.handle_readiness_low(dashboard=dashboard)
    assert "42.5" in answer
    assert "retention gap" in answer.lower()
    assert "3 revision" in answer.lower()
    assert len(sources) >= 2


@pytest.mark.asyncio
async def test_handle_weakest_concepts_lists_items() -> None:
    weaknesses = LearningGraphWeaknessesResponse(
        student_id=uuid4(),
        weaknesses=[
            WeaknessItemResponse(
                concept_id="upsc_cse.polity.basic_structure",
                mastery_score=Decimal("30"),
                retention_score=Decimal("25"),
                importance_score=Decimal("90"),
                weakness_score=Decimal("85"),
            )
        ],
    )
    answer, _ = await student_handlers.handle_weakest_concepts(weaknesses=weaknesses)
    assert "upsc_cse.polity.basic_structure" in answer
    assert "85" in answer


@pytest.mark.asyncio
async def test_handle_goal_on_track_includes_probability() -> None:
    dashboard = TwinDashboardResponse(
        on_track=False,
        projected_readiness=Decimal("55"),
        gap_to_goal=Decimal("15"),
    )
    goal = GoalResponse(
        exam_id="upsc_cse",
        target_readiness_score=Decimal("70"),
        target_date=date(2027, 6, 1),
        daily_capacity_minutes=120,
        goal_probability=Decimal("38"),
        goal_likelihood="unlikely",
    )
    answer, _ = await student_handlers.handle_goal_on_track(dashboard=dashboard, goal=goal)
    assert "not on track" in answer.lower()
    assert "38" in answer


@pytest.mark.asyncio
async def test_handle_study_today_prefers_daily_plan() -> None:
    dashboard = TwinDashboardResponse(due_revision_count=1)
    study_plan = StudyPlanResponse(
        daily_plan=[
            DailyPlanItemResponse(
                concept_id="upsc_cse.history.modern_india",
                activity_type="study_session",
                estimated_minutes=45,
                priority_score=Decimal("80"),
                adaptive_priority=Decimal("82"),
                readiness_gain=Decimal("2.5"),
                adjustment_explanation="High importance concept with low mastery.",
            )
        ]
    )
    answer, _ = await student_handlers.handle_study_today(
        dashboard=dashboard,
        study_plan=study_plan,
        recommendations=[],
    )
    assert "upsc_cse.history.modern_india" in answer
    assert "High importance concept" in answer


@pytest.mark.asyncio
async def test_handle_recommendation_why_uses_top_item() -> None:
    recommendations = [
        TwinRecommendationResponse(
            concept_id="upsc_cse.polity.fundamental_rights",
            recommendation_type="revision",
            recommendation_score=Decimal("91"),
            importance_score=Decimal("88"),
            weakness_score=Decimal("75"),
            retention_score=Decimal("40"),
            readiness_gain=Decimal("3.2"),
            explanation="Retention is below target for a high-importance concept.",
        )
    ]
    answer, _ = await student_handlers.handle_recommendation_why(recommendations=recommendations)
    assert "fundamental_rights" in answer
    assert "Retention is below target" in answer


@pytest.mark.asyncio
async def test_handle_draft_coaching_note_is_template_based() -> None:
    dashboard = TwinDashboardResponse(
        readiness_score=Decimal("48"),
        largest_negative_driver="revision_backlog",
        due_revision_count=4,
        high_risk_concept_count=2,
        mentor_action="contact_student",
        escalation_level="high",
        top_mentor_message="Overdue revisions are slowing readiness growth.",
        on_track=False,
        goal_probability=Decimal("35"),
    )
    answer, sources = await mentor_handlers.handle_draft_coaching_note(
        dashboard=dashboard,
        mentor_case=None,
    )
    assert "DRAFT COACHING NOTE" in answer
    assert "revision backlog" in answer.lower()
    assert "contact student" in answer.lower()
    assert len(sources) >= 1


@pytest.mark.asyncio
async def test_handle_summarize_student_includes_goal() -> None:
    dashboard = TwinDashboardResponse(
        readiness_score=Decimal("60"),
        due_revision_count=1,
        high_risk_concept_count=0,
        recommendation_count=3,
        goal_summary=TwinGoalSummaryResponse(
            target_readiness_score=Decimal("75"),
            target_date=date(2027, 5, 1),
        ),
        generated_at=datetime.now(UTC),
    )
    answer, _ = await mentor_handlers.handle_summarize_student(
        dashboard=dashboard,
        student_id=str(uuid4()),
    )
    assert "Readiness: 60" in answer
    assert "2027-05-01" in answer
