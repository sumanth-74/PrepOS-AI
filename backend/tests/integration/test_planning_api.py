from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_planning_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/planning/generate" in paths
    assert "/api/v1/planning/current" in paths
    assert "/api/v1/planning/history" in paths
    assert "/api/v1/planning/item/{item_id}/complete" in paths
    assert "/api/v1/planning/explain/{concept_id}" in paths
    assert "/api/v1/planning/student/{student_id}" in paths
    assert "/api/v1/planning/student/{student_id}/regenerate" in paths
    assert "/api/v1/admin/planning" in paths
