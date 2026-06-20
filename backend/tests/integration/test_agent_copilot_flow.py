from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.agents.events.workflows import GoalRiskWorkflow, ReadinessDropWorkflow
from prepos.application.copilot.analytics_ports import RecordedCopilotQuery
from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.service import CopilotService
from prepos.core.tenancy import RoleName, TenantContext


def _analytics_mock() -> AsyncMock:
    mock = AsyncMock()
    mock.record_query.return_value = RecordedCopilotQuery(session_id=uuid4(), query_id=uuid4())
    return mock


@pytest.mark.asyncio
async def test_copilot_agent_mode_routes_to_orchestrator() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    student_id = uuid4()
    student = AsyncMock()
    student.id = student_id
    student.user_id = user_id
    student.target_exam_id = "upsc_cse"

    student_uow = AsyncMock()
    student_uow.student_repo.get_by_user_id.return_value = student

    agent_orchestrator = AsyncMock()
    agent_response = AsyncMock()
    agent_response.answer = "Agent synthesized readiness coaching plan."
    agent_response.confidence = "high"
    agent_response.sources = []
    agent_orchestrator.execute.return_value = agent_response

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
        forecasting_service=AsyncMock(),
        intervention_service=AsyncMock(),
        cohort_service=AsyncMock(),
        institution_service=AsyncMock(),
        institution_outcome_service=AsyncMock(),
        agent_orchestrator=agent_orchestrator,
    )

    response = await service.query(
        context=TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            roles=frozenset({RoleName.STUDENT}),
        ),
        request=CopilotQueryRequest(
            persona="student",
            question="How can I improve my readiness?",
            agent_mode=True,
        ),
    )

    assert response.intent == "agent_orchestration"
    assert "Agent synthesized" in response.answer
    agent_orchestrator.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_readiness_drop_workflow_persists_audit_trail() -> None:
    repository = AsyncMock()
    repository.save_workflow.return_value = uuid4()
    repository.record_workflow_event.return_value = uuid4()

    workflow = ReadinessDropWorkflow()
    notification = await workflow.run(
        repository=repository,
        tenant_id=uuid4(),
        subject_key="student_42",
        readiness_delta=-8.5,
    )

    assert notification.event_type == "readiness_drop"
    assert "8.5" in notification.message
    repository.save_workflow.assert_awaited_once()


@pytest.mark.asyncio
async def test_goal_risk_workflow_returns_recommended_actions() -> None:
    repository = AsyncMock()
    repository.save_workflow.return_value = uuid4()

    workflow = GoalRiskWorkflow()
    notification = await workflow.run(
        repository=repository,
        tenant_id=uuid4(),
        subject_key="student_99",
        forecast_probability=42.0,
    )

    assert notification.recommended_actions
    repository.save_workflow.assert_awaited_once()
