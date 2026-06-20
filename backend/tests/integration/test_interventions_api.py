from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_interventions_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/interventions/my-history" in paths
    assert "/api/v1/interventions/student/{student_id}" in paths
    assert "/api/v1/interventions/student/{student_id}/generate" in paths
    assert "/api/v1/interventions/{intervention_id}/execute" in paths
    assert "/api/v1/interventions/{intervention_id}/complete" in paths
    assert "/api/v1/interventions/{intervention_id}/explain" in paths
    assert "/api/v1/admin/interventions" in paths
