from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_institution_outcome_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/admin/institution/initiatives" in paths
    assert "/api/v1/admin/institution/outcomes" in paths
    assert "/api/v1/admin/institution/roi" in paths
    assert "/api/v1/admin/institution/roi/export" in paths
