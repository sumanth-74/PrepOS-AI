from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from prepos.application.copilot.analytics_dto import (
    CopilotAdoptionFunnelItem,
    CopilotAnalyticsResponse,
    CopilotConfidenceDistributionItem,
    CopilotContentAnalyticsResponse,
    CopilotDailyUsageItem,
    CopilotIntentDistributionItem,
    CopilotMentorKnowledgeAnalyticsResponse,
    CopilotPersonaUsageResponse,
    CopilotPromptCountItem,
    CopilotSuccessCriteriaResponse,
)
from prepos.application.copilot.analytics_ports import CopilotAnalyticsRepositoryPort, RecordedCopilotQuery
from prepos.application.copilot.handlers.mentor_knowledge import MENTOR_CONTENT_INTENTS
from prepos.application.copilot.handlers.student_knowledge import STUDENT_CONTENT_INTENTS
from prepos.core.tenancy import RoleName, TenantContext

SESSION_IDLE_MINUTES = 30

CONTENT_EXPLANATION_INTENTS: frozenset[str] = frozenset(
    {
        "explain_concept",
        "define_concept",
        "what_is",
        "explain_topic",
        "content_qna",
        "coaching_guidance",
        "explain_student_weakness",
        "concept_revision_strategy",
        "mentor_content_qna",
    }
)

CONTENT_EXPLANATION_PROXY_KEYWORDS: frozenset[str] = frozenset(
    {
        "explain",
        "what is",
        "what are",
        "define",
        "meaning of",
        "describe",
    }
)


def _quantize_percent(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _resolve_role(context: TenantContext, persona: str) -> str:
    if persona == "student" and context.has_role(RoleName.STUDENT):
        return RoleName.STUDENT.value
    if persona == "mentor":
        if context.has_role(RoleName.FACULTY):
            return RoleName.FACULTY.value
        if context.has_role(RoleName.INSTITUTE_ADMIN):
            return RoleName.INSTITUTE_ADMIN.value
    if persona == "admin" and context.has_role(RoleName.INSTITUTE_ADMIN):
        return RoleName.INSTITUTE_ADMIN.value
    if context.has_role(RoleName.SUPER_ADMIN):
        return RoleName.SUPER_ADMIN.value
    for role in context.roles:
        return role.value
    return "unknown"


class CopilotAnalyticsService:
    def __init__(self, *, repo: CopilotAnalyticsRepositoryPort) -> None:
        self._repo = repo

    async def record_query(
        self,
        *,
        context: TenantContext,
        persona: str,
        intent: str,
        query_text: str,
        response_time_ms: int,
        session_id: UUID | None = None,
        citation_count: int | None = None,
        confidence: str | None = None,
    ) -> RecordedCopilotQuery:
        now = datetime.now(UTC)
        role = _resolve_role(context, persona)
        active_since = now - timedelta(minutes=SESSION_IDLE_MINUTES)

        resolved_session_id = session_id
        if resolved_session_id is not None:
            existing = await self._repo.find_active_session(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                persona=persona,
                active_since=active_since,
            )
            if existing != resolved_session_id:
                resolved_session_id = None

        if resolved_session_id is None:
            existing = await self._repo.find_active_session(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                persona=persona,
                active_since=active_since,
            )
            resolved_session_id = existing or await self._repo.create_session(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                persona=persona,
                role=role,
                started_at=now,
            )

        await self._repo.touch_session(session_id=resolved_session_id, last_activity_at=now)
        query_id = await self._repo.insert_query(
            tenant_id=context.tenant_id,
            session_id=resolved_session_id,
            user_id=context.user_id,
            role=role,
            persona=persona,
            intent=intent,
            query_text=query_text.strip(),
            response_time_ms=response_time_ms,
            created_at=now,
            citation_count=citation_count,
            confidence=confidence,
        )
        await self._repo.upsert_intent_metric(
            tenant_id=context.tenant_id,
            metric_date=now.date(),
            persona=persona,
            intent=intent,
        )
        if persona == "student" and intent in STUDENT_CONTENT_INTENTS:
            await self._repo.upsert_intent_metric(
                tenant_id=context.tenant_id,
                metric_date=now.date(),
                persona=persona,
                intent="content_qna",
            )
        if persona == "mentor" and intent in MENTOR_CONTENT_INTENTS:
            await self._repo.upsert_intent_metric(
                tenant_id=context.tenant_id,
                metric_date=now.date(),
                persona=persona,
                intent="mentor_content_qna",
            )
        return RecordedCopilotQuery(session_id=resolved_session_id, query_id=query_id)

    async def get_analytics(
        self,
        *,
        tenant_id: UUID,
        period_days: int = 30,
    ) -> CopilotAnalyticsResponse:
        period_days = max(1, min(period_days, 365))
        now = datetime.now(UTC)
        since = now - timedelta(days=period_days)
        today = now.date()
        week_start = today - timedelta(days=today.weekday())

        total_queries = await self._repo.count_total_queries(tenant_id, since=since)
        unique_users = await self._repo.count_unique_query_users(tenant_id, since=since)
        total_tenant_users = await self._repo.count_tenant_users(tenant_id)
        unknown_count = await self._repo.count_unknown_queries(tenant_id, since=since)
        dau = await self._repo.count_daily_active_users(tenant_id, on_date=today)
        wau = await self._repo.count_weekly_active_users(
            tenant_id,
            week_start=week_start,
            week_end=today,
        )

        queries_per_user = Decimal("0")
        if unique_users > 0:
            queries_per_user = _quantize_percent(Decimal(total_queries) / Decimal(unique_users))

        unknown_rate = Decimal("0")
        if total_queries > 0:
            unknown_rate = _quantize_percent(Decimal(unknown_count) * Decimal("100") / Decimal(total_queries))

        intent_rows = await self._repo.list_intent_distribution(tenant_id, since=since)
        intent_distribution = [
            CopilotIntentDistributionItem(
                intent=row.intent,
                count=row.count,
                share=_quantize_percent(
                    Decimal(row.count) * Decimal("100") / Decimal(total_queries)
                )
                if total_queries > 0
                else Decimal("0"),
            )
            for row in intent_rows
        ]

        persona_rows = await self._repo.list_persona_usage(tenant_id, since=since)
        persona_map = {row.persona: row for row in persona_rows}

        def _persona_usage(persona: str) -> CopilotPersonaUsageResponse:
            row = persona_map.get(persona)
            count = row.count if row else 0
            users = row.unique_users if row else 0
            share = (
                _quantize_percent(Decimal(count) * Decimal("100") / Decimal(total_queries))
                if total_queries > 0
                else Decimal("0")
            )
            return CopilotPersonaUsageResponse(
                persona=persona,
                query_count=count,
                unique_users=users,
                share_of_queries=share,
            )

        daily_rows = await self._repo.list_daily_usage(tenant_id, since=since)
        daily_usage_trend = [
            CopilotDailyUsageItem(
                date=row.usage_date,
                query_count=row.query_count,
                unique_users=row.unique_users,
            )
            for row in daily_rows
        ]

        top_prompts = [
            CopilotPromptCountItem(query_text=row.query_text, count=row.count)
            for row in await self._repo.list_top_prompts(tenant_id, since=since, limit=10)
        ]
        unknown_intents = [
            CopilotPromptCountItem(query_text=row.query_text, count=row.count)
            for row in await self._repo.list_unknown_prompts(tenant_id, since=since, limit=10)
        ]

        session_count = await self._repo.count_sessions(tenant_id, since=since)
        first_query_users = unique_users
        active_users = await self._repo.count_users_with_min_queries(
            tenant_id,
            since=since,
            min_queries=3,
        )
        power_users = await self._repo.count_users_with_min_queries(
            tenant_id,
            since=since,
            min_queries=5,
        )

        funnel_base = total_tenant_users if total_tenant_users > 0 else 1
        adoption_funnel = [
            CopilotAdoptionFunnelItem(
                stage="registered_users",
                count=total_tenant_users,
                share=_quantize_percent(Decimal(total_tenant_users) * Decimal("100") / Decimal(funnel_base)),
            ),
            CopilotAdoptionFunnelItem(
                stage="copilot_sessions",
                count=session_count,
                share=_quantize_percent(Decimal(session_count) * Decimal("100") / Decimal(funnel_base)),
            ),
            CopilotAdoptionFunnelItem(
                stage="first_query",
                count=first_query_users,
                share=_quantize_percent(Decimal(first_query_users) * Decimal("100") / Decimal(funnel_base)),
            ),
            CopilotAdoptionFunnelItem(
                stage="active_users_3_plus_queries",
                count=active_users,
                share=_quantize_percent(Decimal(active_users) * Decimal("100") / Decimal(funnel_base)),
            ),
            CopilotAdoptionFunnelItem(
                stage="power_users_5_plus_queries",
                count=power_users,
                share=_quantize_percent(Decimal(power_users) * Decimal("100") / Decimal(funnel_base)),
            ),
        ]

        adoption_rate = Decimal("0")
        if total_tenant_users > 0:
            adoption_rate = _quantize_percent(
                Decimal(unique_users) * Decimal("100") / Decimal(total_tenant_users)
            )

        top_five_intents = {item.intent for item in intent_distribution[:5]}
        content_in_top_five = bool(top_five_intents & CONTENT_EXPLANATION_INTENTS)
        proxy_in_top_prompts = any(
            any(keyword in item.query_text.lower() for keyword in CONTENT_EXPLANATION_PROXY_KEYWORDS)
            for item in top_prompts[:5]
        )

        content_questions_period = await self._repo.count_content_queries(tenant_id, since=since)
        content_questions_today = await self._repo.count_content_queries(
            tenant_id,
            since=since,
            on_date=today,
        )
        citation_usage_count = await self._repo.count_queries_with_citations(tenant_id, since=since)
        citation_usage_rate = Decimal("0")
        if content_questions_period > 0:
            citation_usage_rate = _quantize_percent(
                Decimal(citation_usage_count) * Decimal("100") / Decimal(content_questions_period)
            )

        confidence_rows = await self._repo.list_confidence_distribution(tenant_id, since=since)
        confidence_total = sum(row.count for row in confidence_rows)
        confidence_distribution = [
            CopilotConfidenceDistributionItem(
                confidence=row.confidence,
                count=row.count,
                share=_quantize_percent(Decimal(row.count) * Decimal("100") / Decimal(confidence_total))
                if confidence_total > 0
                else Decimal("0"),
            )
            for row in confidence_rows
        ]

        content_daily_rows = await self._repo.list_content_daily_usage(tenant_id, since=since)
        content_daily_usage = [
            CopilotDailyUsageItem(
                date=row.usage_date,
                query_count=row.query_count,
                unique_users=row.unique_users,
            )
            for row in content_daily_rows
        ]

        success_criteria = CopilotSuccessCriteriaResponse(
            active_user_adoption_actual=adoption_rate,
            active_user_adoption_met=adoption_rate >= Decimal("40"),
            unknown_intent_rate_actual=unknown_rate,
            unknown_intent_rate_met=unknown_rate < Decimal("15"),
            queries_per_active_user_actual=queries_per_user,
            queries_per_active_user_met=queries_per_user > Decimal("3"),
            content_explanation_in_top_five_met=content_in_top_five or proxy_in_top_prompts,
            content_explanation_note=(
                "Student content Q&A is routed through the Knowledge Agent with citations."
                if content_in_top_five
                else "Content-explanation intents are available; adoption still building."
            ),
        )

        content_analytics = CopilotContentAnalyticsResponse(
            content_questions_today=content_questions_today,
            content_questions_period=content_questions_period,
            citation_usage_count=citation_usage_count,
            citation_usage_rate=citation_usage_rate,
            confidence_distribution=confidence_distribution,
            content_daily_usage=content_daily_usage,
        )

        mentor_content_questions_period = await self._repo.count_mentor_content_queries(
            tenant_id,
            since=since,
        )
        mentor_content_questions_today = await self._repo.count_mentor_content_queries(
            tenant_id,
            since=since,
            on_date=today,
        )
        mentor_citation_usage_count = await self._repo.count_mentor_queries_with_citations(
            tenant_id,
            since=since,
        )
        mentor_citation_usage_rate = Decimal("0")
        if mentor_content_questions_period > 0:
            mentor_citation_usage_rate = _quantize_percent(
                Decimal(mentor_citation_usage_count)
                * Decimal("100")
                / Decimal(mentor_content_questions_period)
            )

        mentor_confidence_rows = await self._repo.list_mentor_confidence_distribution(
            tenant_id,
            since=since,
        )
        mentor_confidence_total = sum(row.count for row in mentor_confidence_rows)
        mentor_confidence_distribution = [
            CopilotConfidenceDistributionItem(
                confidence=row.confidence,
                count=row.count,
                share=_quantize_percent(
                    Decimal(row.count) * Decimal("100") / Decimal(mentor_confidence_total)
                )
                if mentor_confidence_total > 0
                else Decimal("0"),
            )
            for row in mentor_confidence_rows
        ]

        mentor_content_daily_rows = await self._repo.list_mentor_content_daily_usage(
            tenant_id,
            since=since,
        )
        mentor_content_daily_usage = [
            CopilotDailyUsageItem(
                date=row.usage_date,
                query_count=row.query_count,
                unique_users=row.unique_users,
            )
            for row in mentor_content_daily_rows
        ]

        mentor_content_analytics = CopilotMentorKnowledgeAnalyticsResponse(
            mentor_content_questions_today=mentor_content_questions_today,
            mentor_content_questions_period=mentor_content_questions_period,
            citation_usage_count=mentor_citation_usage_count,
            citation_usage_rate=mentor_citation_usage_rate,
            confidence_distribution=mentor_confidence_distribution,
            mentor_content_daily_usage=mentor_content_daily_usage,
        )

        return CopilotAnalyticsResponse(
            period_days=period_days,
            generated_at=now,
            dau=dau,
            wau=wau,
            total_queries=total_queries,
            unique_copilot_users=unique_users,
            total_tenant_users=total_tenant_users,
            queries_per_user_avg=queries_per_user,
            unknown_intent_rate=unknown_rate,
            student_usage=_persona_usage("student"),
            mentor_usage=_persona_usage("mentor"),
            admin_usage=_persona_usage("admin"),
            intent_distribution=intent_distribution,
            daily_usage_trend=daily_usage_trend,
            top_prompts=top_prompts,
            unknown_intents=unknown_intents,
            adoption_funnel=adoption_funnel,
            success_criteria=success_criteria,
            content_analytics=content_analytics,
            mentor_content_analytics=mentor_content_analytics,
        )

    async def export_csv(
        self,
        *,
        tenant_id: UUID,
        period_days: int = 30,
    ) -> str:
        period_days = max(1, min(period_days, 365))
        since = datetime.now(UTC) - timedelta(days=period_days)
        rows = await self._repo.list_queries_for_export(tenant_id, since=since)
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "query_id",
                "session_id",
                "user_id",
                "role",
                "persona",
                "intent",
                "query_text",
                "response_time_ms",
                "citation_count",
                "confidence",
                "created_at",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return buffer.getvalue()
