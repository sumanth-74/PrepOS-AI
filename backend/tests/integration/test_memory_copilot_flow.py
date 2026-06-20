from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.analytics_ports import RecordedCopilotQuery
from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.service import CopilotService
from prepos.application.memory.memory_context import MemoryContext
from prepos.application.recommendations.recommendation_models import ConceptRecommendation
from prepos.core.tenancy import RoleName, TenantContext


def _analytics_mock() -> AsyncMock:
    mock = AsyncMock()
    session_id = uuid4()
    mock.record_query.return_value = RecordedCopilotQuery(session_id=session_id, query_id=uuid4())
    return mock


@pytest.mark.asyncio
async def test_study_next_injects_memory_context() -> None:
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

    memory_service = AsyncMock()
    memory_service.load_student_context.return_value = MemoryContext(
        context_lines=["Federalism previously improved readiness by +4.2 (effectiveness 1.80)"],
    )

    recommendation_service = AsyncMock()
    recommendation_service.get_recommendations_for_intent.return_value = [
        ConceptRecommendation(
            concept_id="upsc.polity_federalism",
            concept_name="Federalism",
            impact_score=8.7,
            reason_codes=["weakness"],
            reasons=["Weakness score high"],
            estimated_readiness_gain=3.2,
            confidence="high",
        )
    ]

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
        recommendation_service=recommendation_service,
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

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(persona="student", question="What should I study next?"),
    )

    assert response.intent == "study_next"
    assert "Coaching memory context" in response.answer
    assert "Federalism previously improved" in response.answer
    memory_service.load_student_context.assert_awaited_once()
