from __future__ import annotations

import pytest

from prepos.application.memory.milestone_detection import detect_readiness_milestones
from prepos.application.recommendations.outcomes.effectiveness_calculator import (
    calculate_effectiveness_score,
)
from prepos.application.memory.memory_context import MemoryContextBuilder
from prepos.application.memory.memory_models import MemoryRecordResponse
from datetime import UTC, datetime
from uuid import uuid4


def _memory(memory_type: str, value: dict, *, score: float = 0) -> MemoryRecordResponse:
    now = datetime.now(UTC)
    return MemoryRecordResponse(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        persona="student",
        memory_type=memory_type,
        memory_key=f"{memory_type}:test",
        memory_value={**value, "effectiveness_score": score},
        created_at=now,
        updated_at=now,
    )


def test_detect_readiness_milestones_for_plus_five() -> None:
    now = datetime.now(UTC)
    milestones = detect_readiness_milestones(
        previous_readiness=50.0,
        current_readiness=56.0,
        occurred_at=now,
    )
    assert len(milestones) == 1
    assert milestones[0].memory_value["threshold"] == 5


def test_memory_context_builder_includes_outcome_line() -> None:
    builder = MemoryContextBuilder()
    memories = [
        _memory(
            "recommendation_outcomes",
            {"concept_name": "Federalism", "actual_gain": 4.2, "effectiveness_score": 1.8},
            score=1.8,
        )
    ]
    context = builder.build_student_context(memories=memories)
    assert any("Federalism" in line and "+4.2" in line for line in context.context_lines)


def test_effectiveness_score_from_sprint_examples() -> None:
    assert calculate_effectiveness_score(actual_gain=2.0, predicted_gain=2.0) == 1.0
    assert calculate_effectiveness_score(actual_gain=4.0, predicted_gain=2.0) == 2.0
