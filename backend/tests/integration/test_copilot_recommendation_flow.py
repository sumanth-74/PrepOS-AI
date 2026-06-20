from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.analytics_ports import RecordedCopilotQuery
from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.intent_router import route_intent
from prepos.application.copilot.service import CopilotService
from prepos.application.recommendations.recommendation_models import ConceptRecommendation
from prepos.core.tenancy import RoleName, TenantContext


def _analytics_mock() -> AsyncMock:
    mock = AsyncMock()
    session_id = uuid4()
    mock.record_query.return_value = RecordedCopilotQuery(session_id=session_id, query_id=uuid4())
    return mock


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("What should I study next?", "study_next"),
        ("What gives me the biggest score improvement?", "highest_score_improvement"),
        ("Which weak concepts matter most?", "weak_concepts_priority"),
        ("Which topics are important for UPSC?", "important_topics"),
    ],
)
def test_student_recommendation_intent_routing(question: str, expected: str) -> None:
    assert route_intent(persona="student", question=question) == expected


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("What should this student focus on?", "student_focus_areas"),
        ("Which intervention improves readiness fastest?", "highest_impact_intervention"),
    ],
)
def test_mentor_recommendation_intent_routing(question: str, expected: str) -> None:
    assert route_intent(persona="mentor", question=question) == expected


@pytest.mark.asyncio
async def test_copilot_study_next_returns_structured_recommendations() -> None:
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
    student_uow = AsyncMock()
    student_uow.student_repo.get_by_user_id.return_value = student
    student_uow.student_repo.get_by_id.return_value = student

    recommendation_service = AsyncMock()
    recommendation_service.get_recommendations_for_intent.return_value = [
        ConceptRecommendation(
            concept_id="upsc.polity_federalism",
            concept_name="Federalism",
            impact_score=8.7,
            reason_codes=["weakness", "high_pyq_frequency"],
            reasons=["Weakness score high", "Appeared in 14 PYQs"],
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
        request=CopilotQueryRequest(persona="student", question="What should I study next?"),
    )

    assert response.intent == "study_next"
    assert response.recommendations
    assert response.recommendations[0].concept_name == "Federalism"
    assert "Why:" in response.answer
    recommendation_service.get_recommendations_for_intent.assert_awaited_once()
