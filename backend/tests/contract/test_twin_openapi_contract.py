from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_twin_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/twin/recommendations" in paths
    assert "/api/v1/twin/snapshot" in paths
    assert "/api/v1/twin/metrics" in paths
    assert "/api/v1/study-plan" in paths
    assert "get" in paths["/api/v1/study-plan"]
    assert "get" in paths["/api/v1/twin/recommendations"]
    assert "get" in paths["/api/v1/twin/snapshot"]
    assert "get" in paths["/api/v1/twin/metrics"]
