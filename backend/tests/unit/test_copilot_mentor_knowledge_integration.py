from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.analytics_ports import RecordedCopilotQuery
from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.service import CopilotService
from prepos.application.knowledge.confidence import INSUFFICIENT_EVIDENCE_ANSWER
from prepos.application.knowledge.dto import KnowledgeAskCitation, KnowledgeAskRequest, KnowledgeAskResponse
from prepos.application.learning_graph.dto import LearningGraphWeaknessesResponse, WeaknessItemResponse
from prepos.application.memory.memory_context import MemoryContext
from prepos.application.twin.twin_dto import TwinDashboardResponse
from prepos.core.tenancy import RoleName, TenantContext


def _analytics_mock() -> AsyncMock:
    mock = AsyncMock()
    session_id = uuid4()
    mock.record_query.return_value = RecordedCopilotQuery(session_id=session_id, query_id=uuid4())
    return mock


def _mentor_service(*, knowledge_agent_service: AsyncMock) -> CopilotService:
    student = SimpleNamespace(id=uuid4(), user_id=uuid4(), target_exam_id="upsc_cse")
    student_uow = AsyncMock()
    student_uow.student_repo.get_by_id.return_value = student

    twin_read_service = AsyncMock()
    twin_read_service.get_dashboard.return_value = TwinDashboardResponse(
        readiness_score=Decimal("42"),
        largest_negative_driver="revision_backlog",
        top_negative_drivers=["revision_backlog"],
        due_revision_count=2,
        high_risk_concept_count=1,
        recommendation_count=0,
    )

    weaknesses = LearningGraphWeaknessesResponse(
        student_id=student.id,
        weaknesses=[
            WeaknessItemResponse(
                concept_id="polity_federalism",
                mastery_score=Decimal("0.35"),
                retention_score=Decimal("0.40"),
                importance_score=Decimal("0.90"),
                weakness_score=Decimal("0.82"),
            ),
        ],
    )
    learning_graph_read_service = AsyncMock()
    learning_graph_read_service.get_weaknesses.return_value = weaknesses

    memory_service = AsyncMock()
    memory_service.load_mentor_context.return_value = MemoryContext()

    return CopilotService(
        session=AsyncMock(),
        student_uow=student_uow,
        twin_read_service=twin_read_service,
        twin_recommendation_service=AsyncMock(),
        learning_graph_read_service=learning_graph_read_service,
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
        memory_service=memory_service,
        planning_service=AsyncMock(),
        forecasting_service=AsyncMock(),
        intervention_service=AsyncMock(),
        cohort_service=AsyncMock(),
        institution_service=AsyncMock(),
        institution_outcome_service=AsyncMock(),
        agent_orchestrator=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_mentor_explain_concept_uses_knowledge_agent_with_citations() -> None:
    chunk_id = uuid4()
    knowledge_agent = AsyncMock()
    knowledge_agent.ask.return_value = KnowledgeAskResponse(
        answer="Federalism divides power between centre and states.",
        citations=[KnowledgeAskCitation(chunk_id=chunk_id, source_title="Polity Notes")],
        confidence="high",
    )
    service = _mentor_service(knowledge_agent_service=knowledge_agent)
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=frozenset({RoleName.FACULTY}),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(
            persona="mentor",
            question="Explain federalism",
            student_id=uuid4(),
        ),
    )

    assert response.intent == "explain_concept"
    assert response.confidence == "high"
    assert len(response.citations) == 1
    assert response.student_context_used is True
    knowledge_agent.ask.assert_awaited_once()


@pytest.mark.asyncio
async def test_mentor_coaching_guidance_passes_student_context_and_concept_ids() -> None:
    knowledge_agent = AsyncMock()
    knowledge_agent.ask.return_value = KnowledgeAskResponse(
        answer="Coach the student on federalism with spaced revision.",
        citations=[KnowledgeAskCitation(chunk_id=uuid4(), source_title="Polity Notes")],
        confidence="high",
    )
    service = _mentor_service(knowledge_agent_service=knowledge_agent)
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=frozenset({RoleName.FACULTY}),
    )

    await service.query(
        context=context,
        request=CopilotQueryRequest(
            persona="mentor",
            question="Give coaching guidance for federalism",
            student_id=uuid4(),
        ),
    )

    request: KnowledgeAskRequest = knowledge_agent.ask.await_args.kwargs["request"]
    assert request.concept_ids == ["polity_federalism"]
    assert request.student_context is not None
    assert "polity_federalism" in request.retrieval_hints


@pytest.mark.asyncio
async def test_mentor_state_intent_does_not_call_knowledge_agent() -> None:
    knowledge_agent = AsyncMock()
    service = _mentor_service(knowledge_agent_service=knowledge_agent)
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=frozenset({RoleName.FACULTY}),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(
            persona="mentor",
            question="Summarize this student",
            student_id=uuid4(),
        ),
    )

    assert response.intent == "summarize_student"
    knowledge_agent.ask.assert_not_called()


@pytest.mark.asyncio
async def test_mentor_low_confidence_fallback() -> None:
    knowledge_agent = AsyncMock()
    knowledge_agent.ask.return_value = KnowledgeAskResponse(
        answer="Speculative answer.",
        citations=[],
        confidence="low",
    )
    service = _mentor_service(knowledge_agent_service=knowledge_agent)
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=frozenset({RoleName.FACULTY}),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(
            persona="mentor",
            question="Summarize Article 356 for mentoring",
            student_id=uuid4(),
        ),
    )

    assert response.intent == "explain_topic"
    assert response.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert response.confidence == "low"
    assert response.citations == []
