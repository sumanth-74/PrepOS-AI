from __future__ import annotations

from collections.abc import Awaitable, Callable

from prepos.core.database import session_scope
from prepos.core.logging import get_logger
from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.events.envelope import envelope_from_dict, envelope_to_dict
from prepos.infrastructure.db.repositories.event_repository import (
    OutboxRepository,
    ProcessedEventRepository,
)

logger = get_logger(__name__)

EventHandler = Callable[[DomainEventEnvelope], Awaitable[None]]


class EventDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[str, list[tuple[str, EventHandler]]] = {}

    def register(self, event_type: str, consumer_name: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append((consumer_name, handler))

    async def dispatch(self, envelope: DomainEventEnvelope) -> None:
        from prepos.application.twin.rebuild_service import clear_twin_session_debounce

        clear_twin_session_debounce()
        handlers = self._handlers.get(envelope.event_type, [])
        for consumer_name, handler in handlers:
            async with session_scope() as session:
                processed_repo = ProcessedEventRepository(session)
                claimed = await processed_repo.try_claim(
                    consumer_name=consumer_name,
                    envelope=envelope,
                )
                if not claimed:
                    logger.info(
                        "event_duplicate_skipped",
                        event_id=str(envelope.event_id),
                        consumer=consumer_name,
                    )
                    continue
                await handler(envelope)
                logger.info(
                    "event_handled",
                    event_id=str(envelope.event_id),
                    event_type=envelope.event_type,
                    consumer=consumer_name,
                )


dispatcher = EventDispatcher()


async def handle_outbox_publish(outbox_row_id: str, envelope_dict: dict[str, object]) -> None:
    envelope = envelope_from_dict(envelope_dict)
    await dispatcher.dispatch(envelope)


async def publish_pending_outbox_events(*, batch_size: int) -> int:
    published = 0
    async with session_scope() as session:
        repo = OutboxRepository(session)
        pending = await repo.fetch_pending(limit=batch_size)
        for row in pending:
            envelope = DomainEventEnvelope(
                event_id=row.event_id,
                event_version=row.event_version,
                event_type=row.event_type,
                occurred_at=row.occurred_at,
                recorded_at=row.recorded_at,
                tenant_id=row.tenant_id,
                correlation_id=row.correlation_id,
                causation_id=row.causation_id,
                producer=row.producer,
                payload=row.payload,
                metadata=row.metadata_json,
            )
            try:
                from prepos.tasks.event_tasks import dispatch_domain_event

                dispatch_domain_event.delay(
                    str(row.id),
                    envelope_to_dict(envelope),
                )
                await repo.mark_published(row.id)
                published += 1
            except Exception as exc:
                await repo.mark_failed(row.id, str(exc))
                logger.error("outbox_publish_failed", outbox_id=str(row.id), error=str(exc))
    return published
