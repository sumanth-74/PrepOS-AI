from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from prepos.core.config import get_settings
from prepos.core.database import get_session_factory
from prepos.infrastructure.health_checks import (
    check_redis,
    get_celery_worker_status,
    get_outbox_counts,
)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness() -> dict[str, Any]:
    settings = get_settings()
    checks: dict[str, str] = {"api": "ok"}
    try:
        factory = get_session_factory()
        async with factory() as db_session:
            await db_session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    checks["redis"] = await check_redis(settings.redis_url)
    status = "ok" if all(value == "ok" for value in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@router.get("/health/worker")
async def worker_health() -> dict[str, Any]:
    worker = get_celery_worker_status()
    return {
        "status": worker["status"],
        "worker_count": worker["worker_count"],
        "workers": worker["workers"],
        **({"detail": worker["detail"]} if "detail" in worker else {}),
    }


@router.get("/health/outbox")
async def outbox_health() -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        counts = await get_outbox_counts(session)
    status = "ok" if counts["failed"] == 0 else "degraded"
    if counts["pending"] > 100:
        status = "degraded"
    return {"status": status, "counts": counts}


@router.get("/health/ops")
async def ops_health() -> dict[str, Any]:
    ready = await readiness()
    worker = get_celery_worker_status()
    factory = get_session_factory()
    async with factory() as session:
        outbox = await get_outbox_counts(session)

    components = {
        "api": ready["checks"].get("api", "ok"),
        "database": ready["checks"].get("database", "error"),
        "redis": ready["checks"].get("redis", "error"),
        "celery_workers": worker["status"],
        "outbox_pending": outbox["pending"],
        "outbox_failed": outbox["failed"],
    }
    overall = "ok"
    if any(value in {"error", "degraded", "unavailable"} for value in components.values() if isinstance(value, str)):
        overall = "degraded"
    if components["database"] == "error":
        overall = "error"
    if outbox["failed"] > 0:
        overall = "degraded"

    return {
        "status": overall,
        "checks": components,
        "worker": worker,
        "outbox": outbox,
    }
