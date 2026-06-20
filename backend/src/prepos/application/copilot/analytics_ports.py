from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RecordedCopilotQuery:
    session_id: UUID
    query_id: UUID


@dataclass(frozen=True, slots=True)
class IntentCountRow:
    intent: str
    count: int


@dataclass(frozen=True, slots=True)
class PersonaCountRow:
    persona: str
    count: int
    unique_users: int


@dataclass(frozen=True, slots=True)
class DailyUsageRow:
    usage_date: date
    query_count: int
    unique_users: int


@dataclass(frozen=True, slots=True)
class PromptCountRow:
    query_text: str
    count: int


@dataclass(frozen=True, slots=True)
class ConfidenceCountRow:
    confidence: str
    count: int


@dataclass(frozen=True, slots=True)
class AdoptionFunnelRow:
    stage: str
    count: int


class CopilotAnalyticsRepositoryPort(ABC):
    @abstractmethod
    async def find_active_session(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        active_since: datetime,
    ) -> UUID | None:
        raise NotImplementedError

    @abstractmethod
    async def create_session(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        role: str,
        started_at: datetime,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def touch_session(
        self,
        *,
        session_id: UUID,
        last_activity_at: datetime,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
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
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def upsert_intent_metric(
        self,
        *,
        tenant_id: UUID,
        metric_date: date,
        persona: str,
        intent: str,
        increment: int = 1,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def count_tenant_users(self, tenant_id: UUID) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_daily_active_users(
        self,
        tenant_id: UUID,
        *,
        on_date: date,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_weekly_active_users(
        self,
        tenant_id: UUID,
        *,
        week_start: date,
        week_end: date,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_total_queries(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_unique_query_users(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_unknown_queries(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def list_intent_distribution(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[IntentCountRow, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_persona_usage(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[PersonaCountRow, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_daily_usage(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[DailyUsageRow, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_top_prompts(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
        limit: int = 10,
    ) -> tuple[PromptCountRow, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_unknown_prompts(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
        limit: int = 10,
    ) -> tuple[PromptCountRow, ...]:
        raise NotImplementedError

    @abstractmethod
    async def count_sessions(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_users_with_min_queries(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
        min_queries: int,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def list_queries_for_export(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[dict[str, object], ...]:
        raise NotImplementedError

    @abstractmethod
    async def count_content_queries(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
        on_date: date | None = None,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_queries_with_citations(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def list_confidence_distribution(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[ConfidenceCountRow, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_content_daily_usage(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[DailyUsageRow, ...]:
        raise NotImplementedError

    @abstractmethod
    async def count_mentor_content_queries(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
        on_date: date | None = None,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_mentor_queries_with_citations(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def list_mentor_confidence_distribution(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[ConfidenceCountRow, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_mentor_content_daily_usage(
        self,
        tenant_id: UUID,
        *,
        since: datetime,
    ) -> tuple[DailyUsageRow, ...]:
        raise NotImplementedError
