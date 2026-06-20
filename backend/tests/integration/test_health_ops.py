from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_worker_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health/worker")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "unavailable", "error"}
    assert "worker_count" in body
    assert "workers" in body


@pytest.mark.asyncio
async def test_outbox_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health/outbox")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    counts = body["counts"]
    assert "pending" in counts
    assert "published" in counts
    assert "failed" in counts
    assert "total" in counts


@pytest.mark.asyncio
async def test_ops_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health/ops")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded", "error"}
    assert "checks" in body
    assert "worker" in body
    assert "outbox" in body
