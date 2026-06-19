from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_student_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    expected = [
        "/api/v1/students/me",
        "/api/v1/students/{student_id}",
        "/api/v1/students/onboarding/complete",
    ]
    for path in expected:
        assert path in paths, f"Missing OpenAPI path: {path}"
