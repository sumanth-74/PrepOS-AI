from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.analytics_ports import RecordedCopilotQuery
from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.service import CopilotService
from prepos.application.planning.planning_models import AdaptivePlanResponse, PlanItemResponse
from prepos.core.tenancy import RoleName, TenantContext


def _analytics_mock() -> AsyncMock:
    mock = AsyncMock()
    session_id = uuid4()
    mock.record_query.return_value = RecordedCopilotQuery(session_id=session_id, query_id=uuid4())
    return mock


@pytest.mark.asyncio
async def test_today_plan_copilot_uses_adaptive_planning() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    student_id = uuid4()
    context = TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=frozenset({RoleName.STUDENT}),
    )

    student = AsyncMock()
    student.id = student_id
    student.target_exam_id = "upsc_cse"
    student_uow = AsyncMock()
    student_uow.student_repo.get_by_user_id.return_value = student
    student_uow.student_repo.get_by_id.return_value = student

    plan = AdaptivePlanResponse(
        plan_id=uuid4(),
        exam_id="upsc_cse",
        generated_at=datetime.now(UTC),
        valid_from=date.today(),
        valid_to=date.today(),
        readiness_snapshot=55.0,
        forecast_snapshot=62.0,
        status="active",
        today_items=[
            PlanItemResponse(
                id=uuid4(),
                concept_id="upsc.polity_federalism",
                concept_name="Federalism",
                activity_type="WEAKNESS_RECOVERY",
                priority_score=88.5,
                estimated_minutes=45,
                estimated_readiness_gain=3.2,
                confidence="high",
                scheduled_date=date.today(),
                source_reason="unresolved weakness, PYQ frequency",
                completion_status="pending",
            )
        ],
        week_items=[],
        next_week_draft=[],
        total_estimated_gain=3.2,
        daily_minutes_budget=120,
    )

    planning_service = AsyncMock()
    planning_service.get_current_plan.return_value = plan

    service = CopilotService(
        session=AsyncMock(),
        student_uow=student_uow,
        twin_read_service=AsyncMock(),
        twin_recommendation_service=AsyncMock(),
        learning_graph_read_service=AsyncMock(),
        goal_service=AsyncMock(),
        study_plan_service=AsyncMock(),
        mentor_case_read_service=AsyncMock(),
        health_service=AsyncMock(),
        analytics_service=_analytics_mock(),
        knowledge_agent_service=AsyncMock(),
        pyq_service=AsyncMock(),
        recommendation_service=AsyncMock(),
        outcome_service=AsyncMock(),
        outcome_analytics_service=AsyncMock(),
        memory_service=AsyncMock(),
        planning_service=planning_service,
        forecasting_service=AsyncMock(),
        intervention_service=AsyncMock(),
        cohort_service=AsyncMock(),
        institution_service=AsyncMock(),
        institution_outcome_service=AsyncMock(),
        agent_orchestrator=AsyncMock(),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(persona="student", question="What is my plan for today?"),
    )

    assert response.intent == "today_plan"
    assert "Federalism" in response.answer
    assert response.recommendations
    planning_service.get_current_plan.assert_awaited_once()
