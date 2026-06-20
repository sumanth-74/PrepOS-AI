from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from prepos.application.memory.memory_builder import MemoryBuilder


@pytest.mark.asyncio
async def test_memory_builder_extracts_recommendation_outcome_memory() -> None:
    shown_event = AsyncMock(
        concept_id="upsc.polity_federalism",
        impact_score=Decimal("8.0"),
        estimated_gain=Decimal("3.0"),
        metadata_json={"readiness_before": 50.0},
        created_at=datetime.now(UTC),
        id=uuid4(),
    )
    outcome = AsyncMock(
        concept_id="upsc.polity_federalism",
        effectiveness_score=Decimal("1.8"),
        actual_gain=Decimal("4.2"),
        predicted_gain=Decimal("3.0"),
        status="successful",
        readiness_before=Decimal("50"),
        readiness_after=Decimal("54.2"),
        forecast_before=Decimal("55"),
        forecast_after=Decimal("58"),
        weakness_before=Decimal("80"),
        weakness_after=Decimal("35"),
        created_at=datetime.now(UTC),
        id=uuid4(),
    )

    shown_result = MagicMock()
    shown_result.scalars.return_value = [shown_event]
    outcome_result = MagicMock()
    outcome_result.scalars.return_value = [outcome]
    query_result = MagicMock()
    query_result.scalars.return_value = []

    session = AsyncMock()
    session.execute = AsyncMock(side_effect=[shown_result, outcome_result, query_result])

    builder = MemoryBuilder(session=session)
    records = await builder.build_for_user(
        tenant_id=uuid4(),
        user_id=uuid4(),
        persona="student",
        student_id=uuid4(),
    )

    types = {record["memory_type"] for record in records}
    assert "recommendation_outcomes" in types
    assert "recommendation_history" in types
