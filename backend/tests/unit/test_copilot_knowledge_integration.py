from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.analytics_ports import RecordedCopilotQuery
from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.service import CopilotService
from prepos.application.knowledge.confidence import INSUFFICIENT_EVIDENCE_ANSWER
from prepos.application.knowledge.dto import KnowledgeAskCitation, KnowledgeAskResponse
from prepos.core.tenancy import RoleName, TenantContext


def _analytics_mock() -> AsyncMock:
    mock = AsyncMock()
    session_id = uuid4()
    mock.record_query.return_value = RecordedCopilotQuery(session_id=session_id, query_id=uuid4())
    return mock


def _student_service(*, knowledge_agent_service: AsyncMock) -> CopilotService:
    student = AsyncMock()
    student.id = uuid4()
    student.target_exam_id = "upsc_cse"
    student_uow = AsyncMock()
    student_uow.student_repo.get_by_user_id.return_value = student
    student_uow.student_repo.get_by_id.return_value = student

    return CopilotService(
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
        knowledge_agent_service=knowledge_agent_service,
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


@pytest.mark.asyncio
async def test_student_content_route_uses_knowledge_agent() -> None:
    chunk_id = uuid4()
    knowledge_agent = AsyncMock()
    knowledge_agent.ask.return_value = KnowledgeAskResponse(
        answer="Federalism divides power between centre and states.",
        citations=[KnowledgeAskCitation(chunk_id=chunk_id, source_title="Polity Notes")],
        confidence="high",
    )
    service = _student_service(knowledge_agent_service=knowledge_agent)
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=frozenset({RoleName.STUDENT}),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(persona="student", question="Explain federalism"),
    )

    assert response.intent == "explain_concept"
    assert "Federalism" in response.answer
    assert response.confidence == "high"
    assert len(response.citations) == 1
    knowledge_agent.ask.assert_awaited_once()


@pytest.mark.asyncio
async def test_student_state_route_does_not_call_knowledge_agent() -> None:
    knowledge_agent = AsyncMock()
    twin_read_service = AsyncMock()
    twin_read_service.get_dashboard.return_value = SimpleNamespace(
        readiness_score=42,
        largest_negative_driver="revision_backlog",
        top_negative_drivers=[],
        due_revision_count=2,
        high_risk_concept_count=1,
        skip_rate=0.1,
    )
    student = AsyncMock()
    student.id = uuid4()
    student.target_exam_id = "upsc_cse"
    student_uow = AsyncMock()
    student_uow.student_repo.get_by_user_id.return_value = student
    student_uow.student_repo.get_by_id.return_value = student

    service = CopilotService(
        session=AsyncMock(),
        student_uow=student_uow,
        twin_read_service=twin_read_service,
        twin_recommendation_service=AsyncMock(),
        learning_graph_read_service=AsyncMock(),
        goal_service=AsyncMock(),
        study_plan_service=AsyncMock(),
        mentor_case_read_service=AsyncMock(),
        health_service=AsyncMock(),
        analytics_service=_analytics_mock(),
        knowledge_agent_service=knowledge_agent,
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
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=frozenset({RoleName.STUDENT}),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(persona="student", question="Why is my readiness low?"),
    )

    assert response.intent == "readiness_low"
    knowledge_agent.ask.assert_not_called()


@pytest.mark.asyncio
async def test_student_fallback_route_for_low_confidence() -> None:
    knowledge_agent = AsyncMock()
    knowledge_agent.ask.return_value = KnowledgeAskResponse(
        answer="Speculative answer.",
        citations=[],
        confidence="low",
    )
    service = _student_service(knowledge_agent_service=knowledge_agent)
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=frozenset({RoleName.STUDENT}),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(persona="student", question="What is xyzunknowntopic?"),
    )

    assert response.intent == "what_is"
    assert response.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert response.confidence == "low"
    assert response.citations == []
