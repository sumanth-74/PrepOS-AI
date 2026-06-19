from __future__ import annotations

import asyncio

from prepos.core.config import get_settings
from prepos.core.database import create_engine, dispose_engine
from prepos.core.logging import configure_logging
from prepos.events.dispatcher import publish_pending_outbox_events
from prepos.tasks.celery_app import celery_app


@celery_app.task(name="prepos.tasks.outbox_tasks.publish_outbox_batch")  # type: ignore[untyped-decorator]
def publish_outbox_batch() -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    create_engine(settings)

    async def _run() -> int:
        try:
            return await publish_pending_outbox_events(batch_size=settings.outbox_publish_batch_size)
        finally:
            await dispose_engine()

    return asyncio.run(_run())
