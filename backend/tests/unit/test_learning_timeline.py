from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from prepos.application.memory.memory_context import memories_to_timeline
from prepos.application.memory.memory_models import MemoryRecordResponse


def test_learning_timeline_orders_events_descending() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    older = MemoryRecordResponse(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        persona="student",
        memory_type="recommendation_history",
        memory_key="recommendation_history:a:1",
        memory_value={"concept_id": "a", "concept_name": "A"},
        created_at=base,
        updated_at=base,
    )
    newer = MemoryRecordResponse(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        persona="student",
        memory_type="recommendation_outcomes",
        memory_key="recommendation_outcomes:a:2",
        memory_value={"concept_id": "a", "concept_name": "A", "actual_gain": 3.0},
        created_at=base,
        updated_at=base.replace(day=2),
    )
    events = memories_to_timeline([older, newer])
    assert events[0].event_type == "recommendation_outcomes"
    assert "Outcome" in events[0].summary
