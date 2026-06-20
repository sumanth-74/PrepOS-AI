from __future__ import annotations

from typing import Any

from sqlalchemy import text

from prepos.core.config import get_settings
from prepos.infrastructure.health_checks import (
    check_redis,
    get_celery_worker_status,
    get_outbox_counts,
)


class CopilotHealthService:
    async def get_platform_health(self, session: Any) -> dict[str, Any]:
        settings = get_settings()
        checks: dict[str, str | int] = {"api": "ok"}
        try:
            await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "error"

        checks["redis"] = await check_redis(settings.redis_url)
        worker = get_celery_worker_status()
        outbox = await get_outbox_counts(session)

        overall = "ok"
        if any(value == "error" for value in checks.values() if isinstance(value, str)):
            overall = "degraded"
        if checks["database"] == "error":
            overall = "error"
        if worker["status"] != "ok":
            overall = "degraded"
        if outbox["failed"] > 0 or outbox["pending"] > 100:
            overall = "degraded"

        return {
            "status": overall,
            "checks": checks,
            "worker": worker,
            "outbox": outbox,
        }

    async def get_worker_status(self) -> dict[str, Any]:
        return get_celery_worker_status()

    async def get_outbox_status(self, session: Any) -> dict[str, Any]:
        counts = await get_outbox_counts(session)
        status = "ok" if counts["failed"] == 0 else "degraded"
        if counts["pending"] > 100:
            status = "degraded"
        return {"status": status, "counts": counts}

    async def get_deployment_readiness(self, session: Any) -> dict[str, Any]:
        platform = await self.get_platform_health(session)
        checks = platform["checks"]
        worker = platform["worker"]
        outbox = platform["outbox"]

        blockers: list[str] = []
        if checks.get("database") != "ok":
            blockers.append("Database is not reachable.")
        if checks.get("redis") != "ok":
            blockers.append("Redis is not reachable.")
        if worker["status"] != "ok":
            blockers.append("No Celery workers are responding.")
        if outbox["failed"] > 0:
            blockers.append(f"{outbox['failed']} outbox event(s) failed.")
        if outbox["pending"] > 100:
            blockers.append(f"{outbox['pending']} outbox events pending (above threshold).")

        ready = len(blockers) == 0
        return {
            "ready": ready,
            "status": "ready" if ready else "not_ready",
            "blockers": blockers,
            "platform": platform,
        }
