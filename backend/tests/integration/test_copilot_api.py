from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from test_learning_graph_event_handlers import _login_student, _provision_graph_for_student


@pytest.mark.asyncio
async def test_copilot_query_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/copilot/query",
        json={"persona": "student", "question": "What should I study next?"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_copilot_query_resolves_dependency_chain(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Exercise FastAPI DI for get_copilot_service — catches lazy-import NameErrors."""
    await _provision_graph_for_student(client, db_session)
    student_token = await _login_student(
        client,
        slug="lg-event-handlers",
        email="student-lg-events@example.com",
    )
    headers = {"Authorization": f"Bearer {student_token}"}

    response = await client.post(
        "/api/v1/copilot/query",
        headers=headers,
        json={
            "persona": "student",
            "question": "What should I study next?",
            "exam_id": "upsc_cse",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["intent"] == "study_next"
    assert isinstance(payload["answer"], str)
    assert payload["answer"]
