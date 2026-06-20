from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.analytics_ports import RecordedCopilotQuery
from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.service import CopilotService
from prepos.application.forecasting.forecast_models import GoalForecastResponse
from prepos.core.tenancy import RoleName, TenantContext


def _analytics_mock() -> AsyncMock:
    mock = AsyncMock()
    session_id = uuid4()
    mock.record_query.return_value = RecordedCopilotQuery(session_id=session_id, query_id=uuid4())
    return mock


@pytest.mark.asyncio
async def test_goal_forecast_copilot_intent() -> None:
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

    forecast = GoalForecastResponse(
        forecast_id=uuid4(),
        exam_id="upsc_cse",
        forecast_date=date.today(),
        target_date=date.today(),
        current_readiness=62.4,
        projected_readiness=74.1,
        target_readiness=75.0,
        probability_of_success=81.0,
        forecast_status="on_track",
        top_drivers=["Federalism", "Parliament"],
        scenarios=[],
        explanations=["Deterministic forecast explanation."],
        generated_at=datetime.now(UTC),
    )
    forecasting_service = AsyncMock()
    forecasting_service.get_current_forecast.return_value = forecast

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
        planning_service=AsyncMock(),
        forecasting_service=forecasting_service,
        intervention_service=AsyncMock(),
        cohort_service=AsyncMock(),
        institution_service=AsyncMock(),
        institution_outcome_service=AsyncMock(),
        agent_orchestrator=AsyncMock(),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(persona="student", question="Show my goal forecast"),
    )

    assert response.intent == "goal_forecast"
    assert "74.1" in response.answer
    assert "81" in response.answer
