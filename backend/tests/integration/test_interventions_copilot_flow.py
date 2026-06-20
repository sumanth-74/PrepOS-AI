from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.service import CopilotService
from prepos.application.interventions.intervention_models import (
    RecommendedInterventionItem,
    StudentInterventionResponse,
)
from prepos.core.tenancy import RoleName, TenantContext


@pytest.mark.asyncio
async def test_recommended_interventions_copilot_uses_optimizer() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    student_id = uuid4()
    context = TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=frozenset({RoleName.FACULTY}),
    )
    intervention_service = AsyncMock()
    intervention_service.get_student_interventions.return_value = StudentInterventionResponse(
        student_id=student_id,
        exam_id="upsc_cse",
        recommended_interventions=[
            RecommendedInterventionItem(
                intervention_type="concept_revision",
                concept_id="polity_federalism",
                concept="Federalism",
                predicted_gain=3.2,
                priority_score=91.0,
                impact_score=91.0,
                confidence="high",
                reason="Federalism: high weakness + high PYQ frequency",
            )
        ],
        generated_at=datetime.now(UTC),
    )

    student_uow = AsyncMock()
    student = AsyncMock()
    student.user_id = uuid4()
    student_uow.student_repo.get_by_id = AsyncMock(return_value=student)

    analytics_service = AsyncMock()
    analytics_service.record_query = AsyncMock(return_value=AsyncMock(session_id=uuid4()))

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
        analytics_service=analytics_service,
        knowledge_agent_service=AsyncMock(),
        pyq_service=AsyncMock(),
        recommendation_service=AsyncMock(),
        outcome_service=AsyncMock(),
        outcome_analytics_service=AsyncMock(),
        memory_service=AsyncMock(),
        planning_service=AsyncMock(),
        forecasting_service=AsyncMock(),
        intervention_service=intervention_service,
        cohort_service=AsyncMock(),
        institution_service=AsyncMock(),
        institution_outcome_service=AsyncMock(),
        agent_orchestrator=AsyncMock(),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(
            persona="mentor",
            question="Show recommended interventions",
            student_id=str(student_id),
        ),
    )

    assert response.intent == "recommended_interventions"
    assert "Federalism" in response.answer
    intervention_service.get_student_interventions.assert_awaited_once()
