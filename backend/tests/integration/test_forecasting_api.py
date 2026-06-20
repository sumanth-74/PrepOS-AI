from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_forecasting_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/forecasting/generate" in paths
    assert "/api/v1/forecasting/current" in paths
    assert "/api/v1/forecasting/scenarios" in paths
    assert "/api/v1/forecasting/scenario/custom" in paths
    assert "/api/v1/forecasting/explain" in paths
    assert "/api/v1/forecasting/student/{student_id}" in paths
    assert "/api/v1/admin/forecasting" in paths
