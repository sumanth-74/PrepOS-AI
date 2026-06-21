from __future__ import annotations

import json
from datetime import UTC, datetime

from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.core.config import Settings
from prepos.core.logging import get_logger
from prepos.domain_events.bus import EventBusPort
from prepos.domain_events.events import DomainEvent

logger = get_logger(__name__)


class RedisStreamsEventBus(EventBusPort):
    """Redis Streams abstraction for domain events (P11.5)."""

    STREAM_KEY = "prepos:domain_events"

    def __init__(self, *, settings: Settings, repository: PlatformMaturityRepositoryPort | None = None) -> None:
        self._settings = settings
        self._repository = repository

    async def publish(self, event: DomainEvent) -> str:
        stream_id = str(event.event_id)
        payload = {
            "event_type": event.event_type.value,
            "tenant_id": str(event.tenant_id) if event.tenant_id else None,
            "payload": event.payload,
            "occurred_at": event.occurred_at.isoformat(),
        }

        try:
            import redis.asyncio as redis

            client = redis.from_url(self._settings.redis_url)
            try:
                stream_id = await client.xadd(
                    self.STREAM_KEY,
                    {"data": json.dumps(payload)},
                )
                stream_id = stream_id.decode() if isinstance(stream_id, bytes) else str(stream_id)
            finally:
                await client.aclose()
        except Exception as exc:
            logger.warning("redis_stream_publish_fallback", error=str(exc), event_type=event.event_type.value)

        if self._repository is not None:
            await self._repository.save_domain_event_stream_log(
                tenant_id=event.tenant_id,
                event_type=event.event_type.value,
                stream_id=stream_id,
                payload=payload,
                now=datetime.now(UTC),
            )

        logger.info(
            "domain_event_published",
            event_type=event.event_type.value,
            stream_id=stream_id,
            tenant_id=str(event.tenant_id) if event.tenant_id else None,
        )
        return stream_id
