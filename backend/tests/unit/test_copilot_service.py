from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.analytics_ports import RecordedCopilotQuery
from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.service import CopilotService
from prepos.core.exceptions import ValidationError
from prepos.core.tenancy import RoleName, TenantContext


def _analytics_mock() -> AsyncMock:
    mock = AsyncMock()
    session_id = uuid4()
    mock.record_query.return_value = RecordedCopilotQuery(session_id=session_id, query_id=uuid4())
    return mock


@pytest.mark.asyncio
async def test_admin_platform_health_query() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    context = TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=frozenset({RoleName.INSTITUTE_ADMIN}),
    )

    health_service = AsyncMock()
    health_service.get_platform_health.return_value = {
        "status": "ok",
        "checks": {"api": "ok", "database": "ok", "redis": "ok"},
        "worker": {"status": "ok", "worker_count": 1, "workers": ["worker@host"]},
        "outbox": {"pending": 0, "published": 10, "failed": 0, "total": 10},
    }

    service = CopilotService(
        session=AsyncMock(),
        student_uow=AsyncMock(),
        twin_read_service=AsyncMock(),
        twin_recommendation_service=AsyncMock(),
        learning_graph_read_service=AsyncMock(),
        goal_service=AsyncMock(),
        study_plan_service=AsyncMock(),
        mentor_case_read_service=AsyncMock(),
        health_service=health_service,
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
        agent_orchestrator=AsyncMock(),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(persona="admin", question="Platform health"),
    )

    assert response.intent == "platform_health"
    assert "Platform status: ok" in response.answer
    assert any(source.reference == "GET /health/ops" for source in response.sources)
    health_service.get_platform_health.assert_awaited_once()


@pytest.mark.asyncio
async def test_mentor_query_requires_student_id() -> None:
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=frozenset({RoleName.FACULTY}),
    )
    service = CopilotService(
        session=AsyncMock(),
        student_uow=AsyncMock(),
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
        agent_orchestrator=AsyncMock(),
    )

    with pytest.raises(ValidationError, match="student_id"):
        await service.query(
            context=context,
            request=CopilotQueryRequest(persona="mentor", question="Summarize this student"),
        )
