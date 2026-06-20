from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.cohort.cohort_models import CohortMetrics, CohortSummaryResponse
from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.service import CopilotService
from prepos.core.tenancy import RoleName, TenantContext


@pytest.mark.asyncio
async def test_cohort_summary_copilot_intent() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    context = TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=frozenset({RoleName.FACULTY}),
    )
    cohort_service = AsyncMock()
    cohort_service.get_cohort_summary.return_value = CohortSummaryResponse(
        cohort_id="upsc_cse_cohort",
        exam_id="upsc_cse",
        student_count=120,
        segments={"high_performer": 24, "on_track": 52, "at_risk": 30, "critical_risk": 14},
        metrics=CohortMetrics(
            average_readiness=62.0,
            average_forecast=68.0,
            average_gain=1.5,
            goal_attainment_rate=0.55,
            recommendation_effectiveness=60.0,
            planning_adherence=65.0,
            mentor_intervention_success=58.0,
            pyq_preparedness=55.0,
            current_affairs_preparedness=57.0,
            cohort_health_score=64.0,
        ),
        top_risks=["Parliament", "Federalism", "Environment"],
        generated_at=datetime.now(UTC),
    )
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
        cohort_service=cohort_service,
        institution_service=AsyncMock(),
        institution_outcome_service=AsyncMock(),
        agent_orchestrator=AsyncMock(),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(persona="mentor", question="Show cohort summary"),
    )

    assert response.intent == "cohort_summary"
    assert "120" in response.answer
    cohort_service.get_cohort_summary.assert_awaited_once()
