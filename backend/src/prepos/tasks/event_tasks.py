from __future__ import annotations

import asyncio
from typing import Any

from prepos.core.config import get_settings
from prepos.core.database import create_engine, dispose_engine
from prepos.core.logging import configure_logging
from prepos.events.dispatcher import handle_outbox_publish
from prepos.tasks.celery_app import celery_app


@celery_app.task(name="prepos.tasks.event_tasks.dispatch_domain_event")  # type: ignore[untyped-decorator]
def dispatch_domain_event(outbox_row_id: str, envelope_dict: dict[str, Any]) -> None:
    _run_async(handle_outbox_publish(outbox_row_id, envelope_dict))


def _run_async(coro: object) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    create_engine(settings)
    try:
        asyncio.run(coro)  # type: ignore[arg-type]
    finally:
        asyncio.run(dispose_engine())
