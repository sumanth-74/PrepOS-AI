from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cohort_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/cohort/students" in paths
    assert "/api/v1/cohort/segments" in paths
    assert "/api/v1/cohort/risks" in paths
    assert "/api/v1/cohort/trends" in paths
    assert "/api/v1/admin/cohort" in paths
    assert "/api/v1/admin/cohort/export" in paths
