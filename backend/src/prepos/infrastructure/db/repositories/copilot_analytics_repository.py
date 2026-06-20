from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import Date, cast, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.copilot.analytics_ports import (
    ConfidenceCountRow,
    CopilotAnalyticsRepositoryPort,
    DailyUsageRow,
    IntentCountRow,
    PersonaCountRow,
    PromptCountRow,
)
from prepos.infrastructure.db.models.copilot_analytics import (
    CopilotIntentMetricModel,
    CopilotQueryModel,
    CopilotSessionModel,
)
from prepos.infrastructure.db.models.foundation import UserModel

_CONTENT_QUERY_INTENTS: tuple[str, ...] = (
    "explain_concept",
    "define_concept",
    "what_is",
    "explain_topic",
)
_MENTOR_CONTENT_QUERY_INTENTS: tuple[str, ...] = (
    "explain_concept",
    "explain_topic",
    "coaching_guidance",
    "explain_student_weakness",
    "concept_revision_strategy",
)


class SqlAlchemyCopilotAnalyticsRepository(CopilotAnalyticsRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_active_session(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        active_since: datetime,
    ) -> UUID | None:
        stmt = (
            select(CopilotSessionModel.id)
            .where(
                CopilotSessionModel.tenant_id == tenant_id,
                CopilotSessionModel.user_id == user_id,
                CopilotSessionModel.persona == persona,
                CopilotSessionModel.last_activity_at >= active_since,
            )
            .order_by(CopilotSessionModel.last_activity_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return row

    async def create_session(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        role: str,
        started_at: datetime,
    ) -> UUID:
        session_id = uuid4()
        row = CopilotSessionModel(
            id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            persona=persona,
            role=role,
            started_at=started_at,
            last_activity_at=started_at,
            query_count=0,
            created_at=started_at,
            updated_at=started_at,
        )
        self._session.add(row)
        await self._session.flush()
        return session_id

    async def touch_session(
        self,
        *,
        session_id: UUID,
        last_activity_at: datetime,
    ) -> None:
        row = await self._session.get(CopilotSessionModel, session_id)
        if row is None:
            return
        row.last_activity_at = last_activity_at
        row.query_count += 1
        row.updated_at = last_activity_at
        await self._session.flush()

    async def insert_query(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID,
        user_id: UUID,
        role: str,
        persona: str,
        intent: str,
        query_text: str,
        response_time_ms: int,
        created_at: datetime,
        citation_count: int | None = None,
        confidence: str | None = None,
    ) -> UUID:
        query_id = uuid4()
        row = CopilotQueryModel(
            id=query_id,
            tenant_id=tenant_id,
            session_id=session_id,
            user_id=user_id,
            role=role,
            persona=persona,
            intent=intent,
            query_text=query_text,
            response_time_ms=response_time_ms,
            citation_count=citation_count,
            confidence=confidence,
            created_at=created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return query_id

    async def upsert_intent_metric(
        self,
        *,
        tenant_id: UUID,
        metric_date: date,
        persona: str,
        intent: str,
        increment: int = 1,
    ) -> None:
        now = datetime.now(UTC)
        stmt = insert(CopilotIntentMetricModel).values(
            id=uuid4(),
            tenant_id=tenant_id,
            metric_date=metric_date,
            persona=persona,
            intent=intent,
            query_count=increment,
            created_at=now,
            updated_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_copilot_intent_metrics_daily",
            set_={
                "query_count": CopilotIntentMetricModel.query_count + increment,
                "updated_at": now,
            },
        )
        await self._session.execute(stmt)

    async def count_tenant_users(self, tenant_id: UUID) -> int:
        stmt = select(func.count()).select_from(UserModel).where(
            UserModel.tenant_id == tenant_id,
            UserModel.is_active.is_(True),
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def count_daily_active_users(
        self,
        tenant_id: UUID,
        *,
        on_date: date,
    ) -> int:
        start = datetime.combine(on_date, datetime.min.time(), tzinfo=UTC)
        end = start + timedelta(days=1)
        stmt = select(func.count(func.distinct(CopilotQueryModel.user_id))).where(
            CopilotQueryModel.tenant_id == tenant_id,
            CopilotQueryModel.created_at >= start,
            CopilotQueryModel.created_at < end,
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def count_weekly_active_users(
        self,
        tenant_id: UUID,
        *,
        week_start: date,
        week_end: date,
    ) -> int:
        start = datetime.combine(week_start, datetime.min.time(), tzinfo=UTC)
        end = datetime.combine(week_end + timedelta(days=1), datetime.min.time(), tzinfo=UTC)
        stmt = select(func.count(func.distinct(CopilotQueryModel.user_id))).where(
            CopilotQueryModel.tenant_id == tenant_id,
            CopilotQueryModel.created_at >= start,
            CopilotQueryModel.created_at < end,
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def count_total_queries(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        stmt = select(func.count()).select_from(CopilotQueryModel).where(
            CopilotQueryModel.tenant_id == tenant_id,
            CopilotQueryModel.created_at >= since,
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def count_unique_query_users(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        stmt = select(func.count(func.distinct(CopilotQueryModel.user_id))).where(
            CopilotQueryModel.tenant_id == tenant_id,
            CopilotQueryModel.created_at >= since,
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def count_unknown_queries(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        stmt = select(func.count()).select_from(CopilotQueryModel).where(
            CopilotQueryModel.tenant_id == tenant_id,
            CopilotQueryModel.created_at >= since,
            CopilotQueryModel.intent == "unknown",
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def list_intent_distribution(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[IntentCountRow, ...]:
        stmt = (
            select(CopilotQueryModel.intent, func.count())
            .where(
                CopilotQueryModel.tenant_id == tenant_id,
                CopilotQueryModel.created_at >= since,
            )
            .group_by(CopilotQueryModel.intent)
            .order_by(func.count().desc())
        )
        rows = (await self._session.execute(stmt)).all()
        return tuple(IntentCountRow(intent=str(intent), count=int(count)) for intent, count in rows)

    async def list_persona_usage(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[PersonaCountRow, ...]:
        stmt = (
            select(
                CopilotQueryModel.persona,
                func.count(),
                func.count(func.distinct(CopilotQueryModel.user_id)),
            )
            .where(
                CopilotQueryModel.tenant_id == tenant_id,
                CopilotQueryModel.created_at >= since,
            )
            .group_by(CopilotQueryModel.persona)
        )
        rows = (await self._session.execute(stmt)).all()
        return tuple(
            PersonaCountRow(persona=str(persona), count=int(count), unique_users=int(unique_users))
            for persona, count, unique_users in rows
        )

    async def list_daily_usage(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[DailyUsageRow, ...]:
        day_col = cast(CopilotQueryModel.created_at, Date).label("usage_date")
        stmt = (
            select(
                day_col,
                func.count(),
                func.count(func.distinct(CopilotQueryModel.user_id)),
            )
            .where(
                CopilotQueryModel.tenant_id == tenant_id,
                CopilotQueryModel.created_at >= since,
            )
            .group_by(day_col)
            .order_by(day_col)
        )
        rows = (await self._session.execute(stmt)).all()
        return tuple(
            DailyUsageRow(
                usage_date=usage_date,
                query_count=int(query_count),
                unique_users=int(unique_users),
            )
            for usage_date, query_count, unique_users in rows
        )

    async def list_top_prompts(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
        limit: int = 10,
    ) -> tuple[PromptCountRow, ...]:
        stmt = (
            select(CopilotQueryModel.query_text, func.count())
            .where(
                CopilotQueryModel.tenant_id == tenant_id,
                CopilotQueryModel.created_at >= since,
            )
            .group_by(CopilotQueryModel.query_text)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return tuple(PromptCountRow(query_text=text, count=int(count)) for text, count in rows)

    async def list_unknown_prompts(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
        limit: int = 10,
    ) -> tuple[PromptCountRow, ...]:
        stmt = (
            select(CopilotQueryModel.query_text, func.count())
            .where(
                CopilotQueryModel.tenant_id == tenant_id,
                CopilotQueryModel.created_at >= since,
                CopilotQueryModel.intent == "unknown",
            )
            .group_by(CopilotQueryModel.query_text)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return tuple(PromptCountRow(query_text=text, count=int(count)) for text, count in rows)

    async def count_sessions(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        stmt = select(func.count()).select_from(CopilotSessionModel).where(
            CopilotSessionModel.tenant_id == tenant_id,
            CopilotSessionModel.started_at >= since,
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def count_users_with_min_queries(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
        min_queries: int,
    ) -> int:
        subq = (
            select(CopilotQueryModel.user_id)
            .where(
                CopilotQueryModel.tenant_id == tenant_id,
                CopilotQueryModel.created_at >= since,
            )
            .group_by(CopilotQueryModel.user_id)
            .having(func.count() >= min_queries)
            .subquery()
        )
        stmt = select(func.count()).select_from(subq)
        return int((await self._session.execute(stmt)).scalar_one())

    async def list_queries_for_export(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[dict[str, object], ...]:
        stmt = (
            select(CopilotQueryModel)
            .where(
                CopilotQueryModel.tenant_id == tenant_id,
                CopilotQueryModel.created_at >= since,
            )
            .order_by(CopilotQueryModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return tuple(
            {
                "query_id": str(row.id),
                "session_id": str(row.session_id),
                "user_id": str(row.user_id),
                "role": row.role,
                "persona": row.persona,
                "intent": row.intent,
                "query_text": row.query_text,
                "response_time_ms": row.response_time_ms,
                "citation_count": row.citation_count,
                "confidence": row.confidence,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        )

    async def count_content_queries(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
        on_date: date | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(CopilotQueryModel).where(
            CopilotQueryModel.tenant_id == tenant_id,
            CopilotQueryModel.created_at >= since,
            CopilotQueryModel.intent.in_(_CONTENT_QUERY_INTENTS),
        )
        if on_date is not None:
            start = datetime.combine(on_date, datetime.min.time(), tzinfo=UTC)
            end = start + timedelta(days=1)
            stmt = stmt.where(
                CopilotQueryModel.created_at >= start,
                CopilotQueryModel.created_at < end,
            )
        return int((await self._session.execute(stmt)).scalar_one())

    async def count_queries_with_citations(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        stmt = select(func.count()).select_from(CopilotQueryModel).where(
            CopilotQueryModel.tenant_id == tenant_id,
            CopilotQueryModel.created_at >= since,
            CopilotQueryModel.citation_count.is_not(None),
            CopilotQueryModel.citation_count > 0,
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def list_confidence_distribution(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[ConfidenceCountRow, ...]:
        stmt = (
            select(CopilotQueryModel.confidence, func.count())
            .where(
                CopilotQueryModel.tenant_id == tenant_id,
                CopilotQueryModel.created_at >= since,
                CopilotQueryModel.intent.in_(_CONTENT_QUERY_INTENTS),
                CopilotQueryModel.confidence.is_not(None),
            )
            .group_by(CopilotQueryModel.confidence)
            .order_by(func.count().desc())
        )
        rows = (await self._session.execute(stmt)).all()
        return tuple(
            ConfidenceCountRow(confidence=str(confidence), count=int(count))
            for confidence, count in rows
        )

    async def list_content_daily_usage(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[DailyUsageRow, ...]:
        day_col = cast(CopilotQueryModel.created_at, Date).label("usage_date")
        stmt = (
            select(
                day_col,
                func.count(),
                func.count(func.distinct(CopilotQueryModel.user_id)),
            )
            .where(
                CopilotQueryModel.tenant_id == tenant_id,
                CopilotQueryModel.created_at >= since,
                CopilotQueryModel.intent.in_(_CONTENT_QUERY_INTENTS),
            )
            .group_by(day_col)
            .order_by(day_col)
        )
        rows = (await self._session.execute(stmt)).all()
        return tuple(
            DailyUsageRow(
                usage_date=usage_date,
                query_count=int(query_count),
                unique_users=int(unique_users),
            )
            for usage_date, query_count, unique_users in rows
        )

    async def count_mentor_content_queries(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
        on_date: date | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(CopilotQueryModel).where(
            CopilotQueryModel.tenant_id == tenant_id,
            CopilotQueryModel.created_at >= since,
            CopilotQueryModel.persona == "mentor",
            CopilotQueryModel.intent.in_(_MENTOR_CONTENT_QUERY_INTENTS),
        )
        if on_date is not None:
            start = datetime.combine(on_date, datetime.min.time(), tzinfo=UTC)
            end = start + timedelta(days=1)
            stmt = stmt.where(
                CopilotQueryModel.created_at >= start,
                CopilotQueryModel.created_at < end,
            )
        return int((await self._session.execute(stmt)).scalar_one())

    async def count_mentor_queries_with_citations(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        stmt = select(func.count()).select_from(CopilotQueryModel).where(
            CopilotQueryModel.tenant_id == tenant_id,
            CopilotQueryModel.created_at >= since,
            CopilotQueryModel.persona == "mentor",
            CopilotQueryModel.intent.in_(_MENTOR_CONTENT_QUERY_INTENTS),
            CopilotQueryModel.citation_count.is_not(None),
            CopilotQueryModel.citation_count > 0,
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def list_mentor_confidence_distribution(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[ConfidenceCountRow, ...]:
        stmt = (
            select(CopilotQueryModel.confidence, func.count())
            .where(
                CopilotQueryModel.tenant_id == tenant_id,
                CopilotQueryModel.created_at >= since,
                CopilotQueryModel.persona == "mentor",
                CopilotQueryModel.intent.in_(_MENTOR_CONTENT_QUERY_INTENTS),
                CopilotQueryModel.confidence.is_not(None),
            )
            .group_by(CopilotQueryModel.confidence)
            .order_by(func.count().desc())
        )
        rows = (await self._session.execute(stmt)).all()
        return tuple(
            ConfidenceCountRow(confidence=str(confidence), count=int(count))
            for confidence, count in rows
        )

    async def list_mentor_content_daily_usage(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[DailyUsageRow, ...]:
        day_col = cast(CopilotQueryModel.created_at, Date).label("usage_date")
        stmt = (
            select(
                day_col,
                func.count(),
                func.count(func.distinct(CopilotQueryModel.user_id)),
            )
            .where(
                CopilotQueryModel.tenant_id == tenant_id,
                CopilotQueryModel.created_at >= since,
                CopilotQueryModel.persona == "mentor",
                CopilotQueryModel.intent.in_(_MENTOR_CONTENT_QUERY_INTENTS),
            )
            .group_by(day_col)
            .order_by(day_col)
        )
        rows = (await self._session.execute(stmt)).all()
        return tuple(
            DailyUsageRow(
                usage_date=usage_date,
                query_count=int(query_count),
                unique_users=int(unique_users),
            )
            for usage_date, query_count, unique_users in rows
        )
