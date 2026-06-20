from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_copilot_analytics_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/admin/copilot/analytics" in paths
    assert "/api/v1/admin/copilot/analytics/export" in paths
    assert "get" in paths["/api/v1/admin/copilot/analytics"]
    assert "get" in paths["/api/v1/admin/copilot/analytics/export"]
