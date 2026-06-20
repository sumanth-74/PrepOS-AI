from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient

from prepos.application.memory.milestone_detection import detect_readiness_milestones
from prepos.application.memory.memory_context import MemoryContextBuilder
from prepos.application.memory.memory_models import MemoryRecordResponse


@pytest.mark.asyncio
async def test_memory_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/memory/student" in paths
    assert "/api/v1/memory/student/timeline" in paths
    assert "/api/v1/memory/mentor/{student_id}" in paths
    assert "/api/v1/memory/milestones" in paths
    assert "/api/v1/memory/rebuild" in paths
    assert "/api/v1/admin/memory" in paths


def test_golden_memory_reconstruction_for_one_hundred_students() -> None:
    builder = MemoryContextBuilder()
    now = datetime.now(UTC)

    for index in range(100):
        readiness_before = 40.0 + index * 0.2
        readiness_after = readiness_before + (index % 8)
        milestones = detect_readiness_milestones(
            previous_readiness=readiness_before,
            current_readiness=readiness_after,
            occurred_at=now,
        )
        memories = [
            MemoryRecordResponse(
                id=uuid4(),
                tenant_id=uuid4(),
                user_id=uuid4(),
                persona="student",
                memory_type="recommendation_outcomes",
                memory_key=f"outcome:{index}",
                memory_value={
                    "concept_name": f"Topic {index}",
                    "actual_gain": readiness_after - readiness_before,
                    "effectiveness_score": 1.0 + (index % 3) * 0.2,
                },
                created_at=now,
                updated_at=now,
            ),
            *[
                MemoryRecordResponse(
                    id=uuid4(),
                    tenant_id=uuid4(),
                    user_id=uuid4(),
                    persona="student",
                    memory_type="progress_milestones",
                    memory_key=item.memory_key,
                    memory_value=item.memory_value,
                    created_at=now,
                    updated_at=now,
                )
                for item in milestones
            ],
        ]
        first = builder.build_student_context(memories=memories)
        second = builder.build_student_context(memories=memories)
        assert first.context_lines == second.context_lines
