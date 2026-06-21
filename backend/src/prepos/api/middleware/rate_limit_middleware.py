from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from prepos.core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_LIMITS: dict[str, int] = {
    "copilot": 60,
    "knowledge_search": 120,
    "knowledge_ask": 60,
    "forecasting": 30,
    "planning": 30,
}

PATH_TO_GROUP: list[tuple[str, str]] = [
    ("/api/v1/copilot", "copilot"),
    ("/api/v1/knowledge/search", "knowledge_search"),
    ("/api/v1/knowledge/ask", "knowledge_ask"),
    ("/api/v1/forecasting", "forecasting"),
    ("/api/v1/planning", "planning"),
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Configurable per-endpoint-group rate limiting (P11.7)."""

    def __init__(
        self,
        app: object,
        *,
        limits: dict[str, int] | None = None,
        record_callback: Callable[..., object] | None = None,
    ) -> None:
        super().__init__(app)
        self._limits = limits or DEFAULT_LIMITS
        self._counters: dict[str, tuple[int, float]] = {}
        self._record_callback = record_callback

    def _resolve_group(self, path: str) -> str | None:
        for prefix, group in PATH_TO_GROUP:
            if path.startswith(prefix):
                return group
        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        group = self._resolve_group(request.url.path)
        if group is None:
            return await call_next(request)

        tenant_id = request.headers.get("x-tenant-id", "anonymous")
        key = f"{tenant_id}:{group}"
        limit = self._limits.get(group, 60)
        now = time.time()
        window_start = int(now // 60)

        counter_key = f"{key}:{window_start}"
        count, _ = self._counters.get(counter_key, (0, now))
        count += 1
        self._counters[counter_key] = (count, now)

        if count > limit:
            logger.warning("rate_limit_exceeded", group=group, tenant_id=tenant_id, count=count, limit=limit)
            if self._record_callback is not None:
                try:
                    await self._record_callback(
                        tenant_id=tenant_id,
                        endpoint_group=group,
                        request_count=count,
                        limit_value=limit,
                        blocked=True,
                    )
                except Exception:
                    pass
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded for {group}. Limit: {limit}/min"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response
