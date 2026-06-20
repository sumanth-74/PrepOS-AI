from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.dto import CopilotQueryRequest
from prepos.application.copilot.service import CopilotService
from prepos.application.institution.institution_models import (
    InstitutionDashboardResponse,
    InstitutionInsightsResponse,
    InstitutionKpis,
    InstitutionRecommendationsResponse,
)
from prepos.core.tenancy import RoleName, TenantContext


@pytest.mark.asyncio
async def test_institution_summary_copilot_intent() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    context = TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=frozenset({RoleName.INSTITUTE_ADMIN}),
    )
    institution_service = AsyncMock()
    institution_service.get_dashboard.return_value = InstitutionDashboardResponse(
        kpis=InstitutionKpis(
            total_students=500,
            total_cohorts=4,
            average_readiness=62.0,
            average_forecast=68.0,
            average_cohort_health=64.0,
            at_risk_students=80,
            intervention_roi=58.0,
            institution_health_score=66.0,
        ),
        cohort_comparisons=[],
        weak_concepts=["Federalism", "Parliament"],
        top_insights=[],
        top_recommendations=[],
        generated_at=datetime.now(UTC),
    )
    institution_service.get_insights.return_value = InstitutionInsightsResponse(
        insights=[],
        total=0,
        generated_at=datetime.now(UTC),
    )
    institution_service.get_recommendations.return_value = InstitutionRecommendationsResponse(
        recommendations=[],
        total=0,
        generated_at=datetime.now(UTC),
    )
    institution_service.get_trends = AsyncMock()
    institution_service.get_mentor_effectiveness = AsyncMock()

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
        institution_service=institution_service,
        institution_outcome_service=AsyncMock(),
        agent_orchestrator=AsyncMock(),
    )

    response = await service.query(
        context=context,
        request=CopilotQueryRequest(persona="admin", question="Show institution summary"),
    )

    assert response.intent == "institution_summary"
    assert "66" in response.answer
    institution_service.get_dashboard.assert_awaited_once()
