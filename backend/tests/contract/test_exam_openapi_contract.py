from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_exam_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    expected = [
        "/api/v1/exams",
        "/api/v1/exams/{exam_id}",
        "/api/v1/syllabus/{exam_id}/tree",
        "/api/v1/syllabus/{exam_id}/catalog/versions/{version}/publish",
        "/api/v1/syllabus/seed/import",
        "/api/v1/concepts/search",
        "/api/v1/concepts/{concept_id}",
        "/api/v1/concepts/{concept_id}/ancestors",
        "/api/v1/concepts/{concept_id}/descendants",
    ]
    for path in expected:
        assert path in paths, f"Missing OpenAPI path: {path}"
