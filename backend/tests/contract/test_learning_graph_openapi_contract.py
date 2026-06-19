from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_learning_graph_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    expected = [
        "/api/v1/learning-graph",
        "/api/v1/learning-graph/summary",
        "/api/v1/learning-graph/nodes/{concept_id}",
        "/api/v1/learning-graph/weaknesses",
        "/api/v1/learning-graph/revisions/due",
        "/api/v1/learning-graph/revisions/queue",
        "/api/v1/learning-graph/readiness",
    ]
    for path in expected:
        assert path in paths, f"Missing OpenAPI path: {path}"

    assert "get" in paths["/api/v1/learning-graph"]
    assert "get" in paths["/api/v1/learning-graph/summary"]
    assert "get" in paths["/api/v1/learning-graph/nodes/{concept_id}"]
    assert "get" in paths["/api/v1/learning-graph/weaknesses"]
    assert "get" in paths["/api/v1/learning-graph/revisions/due"]
    assert "get" in paths["/api/v1/learning-graph/revisions/queue"]
    assert "get" in paths["/api/v1/learning-graph/readiness"]
