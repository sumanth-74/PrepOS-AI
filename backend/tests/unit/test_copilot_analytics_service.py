from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.analytics_ports import (
    DailyUsageRow,
    IntentCountRow,
    PersonaCountRow,
    PromptCountRow,
)
from prepos.application.copilot.analytics_service import CopilotAnalyticsService
from prepos.core.tenancy import RoleName, TenantContext


@pytest.mark.asyncio
async def test_record_query_creates_session_when_missing() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    session_id = uuid4()
    repo = AsyncMock()
    repo.find_active_session.return_value = None
    repo.create_session.return_value = session_id
    repo.insert_query.return_value = uuid4()

    service = CopilotAnalyticsService(repo=repo)
    context = TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=frozenset({RoleName.STUDENT}),
    )

    recorded = await service.record_query(
        context=context,
        persona="student",
        intent="study_today",
        query_text="What should I study today?",
        response_time_ms=42,
    )

    assert recorded.session_id == session_id
    repo.create_session.assert_awaited_once()
    repo.upsert_intent_metric.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_analytics_computes_unknown_rate() -> None:
    tenant_id = uuid4()
    repo = AsyncMock()
    repo.count_total_queries.return_value = 10
    repo.count_unique_query_users.return_value = 4
    repo.count_tenant_users.return_value = 20
    repo.count_unknown_queries.return_value = 2
    repo.count_daily_active_users.return_value = 3
    repo.count_weekly_active_users.return_value = 5
    repo.list_intent_distribution.return_value = (
        IntentCountRow(intent="study_today", count=5),
        IntentCountRow(intent="unknown", count=2),
    )
    repo.list_persona_usage.return_value = (
        PersonaCountRow(persona="student", count=8, unique_users=3),
    )
    repo.list_daily_usage.return_value = (
        DailyUsageRow(usage_date=date.today(), query_count=4, unique_users=2),
    )
    repo.list_top_prompts.return_value = (
        PromptCountRow(query_text="What should I study today?", count=3),
    )
    repo.list_unknown_prompts.return_value = (
        PromptCountRow(query_text="Explain federalism", count=2),
    )
    repo.count_sessions.return_value = 6
    repo.count_users_with_min_queries.side_effect = [2, 1]
    repo.count_content_queries.return_value = 3
    repo.count_queries_with_citations.return_value = 2
    repo.list_confidence_distribution.return_value = ()
    repo.list_content_daily_usage.return_value = (
        DailyUsageRow(usage_date=date.today(), query_count=1, unique_users=1),
    )
    repo.count_mentor_content_queries.return_value = 2
    repo.count_mentor_queries_with_citations.return_value = 1
    repo.list_mentor_confidence_distribution.return_value = ()
    repo.list_mentor_content_daily_usage.return_value = ()

    service = CopilotAnalyticsService(repo=repo)
    analytics = await service.get_analytics(tenant_id=tenant_id, period_days=30)

    assert analytics.total_queries == 10
    assert analytics.unknown_intent_rate == Decimal("20.00")
    assert analytics.queries_per_user_avg == Decimal("2.50")
    assert analytics.student_usage.query_count == 8
    assert analytics.content_analytics.content_questions_period == 3
    assert analytics.content_analytics.citation_usage_count == 2
    assert analytics.mentor_content_analytics.mentor_content_questions_period == 2
    assert analytics.success_criteria.unknown_intent_rate_met is False


@pytest.mark.asyncio
async def test_record_query_tracks_content_qna_metric() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    session_id = uuid4()
    repo = AsyncMock()
    repo.find_active_session.return_value = None
    repo.create_session.return_value = session_id
    repo.insert_query.return_value = uuid4()

    service = CopilotAnalyticsService(repo=repo)
    context = TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=frozenset({RoleName.STUDENT}),
    )

    await service.record_query(
        context=context,
        persona="student",
        intent="explain_concept",
        query_text="Explain federalism",
        response_time_ms=120,
        citation_count=2,
        confidence="high",
    )

    assert repo.insert_query.await_args.kwargs["citation_count"] == 2
    assert repo.insert_query.await_args.kwargs["confidence"] == "high"
    assert repo.upsert_intent_metric.await_count == 2
    metric_intents = [call.kwargs["intent"] for call in repo.upsert_intent_metric.await_args_list]
    assert "explain_concept" in metric_intents
    assert "content_qna" in metric_intents


@pytest.mark.asyncio
async def test_record_query_tracks_mentor_content_qna_metric() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    session_id = uuid4()
    repo = AsyncMock()
    repo.find_active_session.return_value = None
    repo.create_session.return_value = session_id
    repo.insert_query.return_value = uuid4()

    service = CopilotAnalyticsService(repo=repo)
    context = TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=frozenset({RoleName.FACULTY}),
    )

    await service.record_query(
        context=context,
        persona="mentor",
        intent="coaching_guidance",
        query_text="Give coaching guidance for federalism",
        response_time_ms=90,
        citation_count=1,
        confidence="high",
    )

    metric_intents = [call.kwargs["intent"] for call in repo.upsert_intent_metric.await_args_list]
    assert "coaching_guidance" in metric_intents
    assert "mentor_content_qna" in metric_intents


@pytest.mark.asyncio
async def test_export_csv_contains_header() -> None:
    tenant_id = uuid4()
    repo = AsyncMock()
    repo.list_queries_for_export.return_value = (
        {
            "query_id": str(uuid4()),
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "role": "student",
            "persona": "student",
            "intent": "study_today",
            "query_text": "What should I study today?",
            "response_time_ms": 10,
            "created_at": datetime.now(UTC).isoformat(),
        },
    )
    service = CopilotAnalyticsService(repo=repo)
    csv_body = await service.export_csv(tenant_id=tenant_id, period_days=7)
    assert "query_id,session_id,user_id,role,persona,intent,query_text" in csv_body
    assert "study_today" in csv_body
