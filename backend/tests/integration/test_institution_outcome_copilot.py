from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.service import CopilotService
from prepos.application.institution_outcomes.outcome_models import OutcomesResponse, RoiResponse
from prepos.core.tenancy import RoleName, TenantContext


@pytest.mark.asyncio
async def test_best_initiatives_copilot_intent() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    context = TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=frozenset({RoleName.INSTITUTE_ADMIN}),
    )
    outcome_service = AsyncMock()
    outcome_service.get_outcomes.return_value = OutcomesResponse(
        outcomes=[],
        total=0,
        average_readiness_uplift=4.5,
        average_forecast_uplift=3.2,
        average_risk_reduction=2.0,
        generated_at=datetime.now(UTC),
    )
    outcome_service.get_roi.return_value = RoiResponse(
        items=[],
        total=0,
        average_roi_score=72.0,
        best_initiatives=[],
        failed_initiatives=[],
        generated_at=datetime.now(UTC),
    )
    outcome_service.get_effectiveness = AsyncMock()

    analytics_service = AsyncMock()
    analytics_service.record_query = AsyncMock(return_value=AsyncMock(session_id=uuid4()))

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
        analytics_service=analytics_service,
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
        institution_outcome_service=outcome_service,
        agent_orchestrator=AsyncMock(),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(persona="admin", question="Which initiatives worked best?"),
    )

    assert response.intent == "best_initiatives"
    outcome_service.get_roi.assert_awaited_once()
