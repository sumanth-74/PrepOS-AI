from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_institution_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/admin/institution" in paths
    assert "/api/v1/admin/institution/insights" in paths
    assert "/api/v1/admin/institution/recommendations" in paths
    assert "/api/v1/admin/institution/trends" in paths
    assert "/api/v1/admin/institution/mentor-effectiveness" in paths
    assert "/api/v1/admin/institution/export" in paths
