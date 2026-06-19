from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.infrastructure.db.models.foundation import OutboxEventModel, ProcessedEventModel


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue(self, envelope: DomainEventEnvelope) -> None:
        row = OutboxEventModel(
            id=uuid4(),
            event_id=envelope.event_id,
            event_version=envelope.event_version,
            event_type=envelope.event_type,
            occurred_at=envelope.occurred_at,
            recorded_at=envelope.recorded_at,
            tenant_id=envelope.tenant_id,
            correlation_id=envelope.correlation_id,
            causation_id=envelope.causation_id,
            producer=envelope.producer,
            payload=envelope.payload,
            metadata_json=envelope.metadata,
            status="pending",
            publish_attempts=0,
        )
        self._session.add(row)
        await self._session.flush()

    async def fetch_pending(self, *, limit: int) -> list[OutboxEventModel]:
        result = await self._session.execute(
            select(OutboxEventModel)
            .where(OutboxEventModel.status == "pending")
            .order_by(OutboxEventModel.recorded_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_published(self, outbox_id: UUID) -> None:
        await self._session.execute(
            update(OutboxEventModel)
            .where(OutboxEventModel.id == outbox_id)
            .values(status="published", published_at=datetime.now(UTC))
        )

    async def mark_failed(self, outbox_id: UUID, error: str) -> None:
        row = await self._session.get(OutboxEventModel, outbox_id)
        if row is None:
            return
        row.status = "failed"
        row.publish_attempts += 1
        row.last_error = error[:2000]
        await self._session.flush()


class ProcessedEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def try_claim(self, *, consumer_name: str, envelope: DomainEventEnvelope) -> bool:
        stmt = (
            insert(ProcessedEventModel)
            .values(
                id=uuid4(),
                consumer_name=consumer_name,
                event_id=envelope.event_id,
                event_type=envelope.event_type,
                processed_at=datetime.now(UTC),
            )
            .on_conflict_do_nothing(index_elements=["consumer_name", "event_id"])
            .returning(ProcessedEventModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
