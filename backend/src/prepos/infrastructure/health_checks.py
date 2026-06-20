from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.infrastructure.db.models.foundation import OutboxEventModel
from prepos.tasks.celery_app import celery_app


async def get_outbox_counts(session: AsyncSession) -> dict[str, int]:
    result = await session.execute(
        select(OutboxEventModel.status, func.count())
        .group_by(OutboxEventModel.status)
    )
    counts = {status: count for status, count in result.all()}
    return {
        "pending": int(counts.get("pending", 0)),
        "published": int(counts.get("published", 0)),
        "failed": int(counts.get("failed", 0)),
        "total": int(sum(counts.values())),
    }


def get_celery_worker_status() -> dict[str, Any]:
    try:
        inspect = celery_app.control.inspect(timeout=1.0)
        ping = inspect.ping()
        if not ping:
            return {
                "status": "unavailable",
                "worker_count": 0,
                "workers": [],
            }
        workers = sorted(ping.keys())
        return {
            "status": "ok",
            "worker_count": len(workers),
            "workers": workers,
        }
    except Exception as exc:
        return {
            "status": "error",
            "worker_count": 0,
            "workers": [],
            "detail": str(exc),
        }


async def check_redis(url: str) -> str:
    try:
        import redis.asyncio as redis

        client = redis.from_url(url, socket_connect_timeout=1.0)
        try:
            pong = await client.ping()
            return "ok" if pong else "error"
        finally:
            await client.aclose()
    except Exception:
        return "error"
