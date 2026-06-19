from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from prepos.core.database import get_session_factory

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness() -> dict[str, Any]:
    checks: dict[str, str] = {"api": "ok"}
    try:
        factory = get_session_factory()
        async with factory() as db_session:
            await db_session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    status = "ok" if all(value == "ok" for value in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
