from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_rag_quality_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/admin/rag-quality" in paths
    assert "/api/v1/admin/rag-quality/export" in paths
    assert "get" in paths["/api/v1/admin/rag-quality"]
    assert "get" in paths["/api/v1/admin/rag-quality/export"]
