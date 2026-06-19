from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.events.handlers import goal_handlers


@pytest.mark.asyncio
async def test_forecast_updated_requests_forecast_projection() -> None:
    envelope = DomainEventEnvelope(
        event_id=uuid4(),
        event_version=1,
        event_type="ForecastUpdated",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=uuid4(),
        correlation_id="corr",
        causation_id="cause",
        producer="forecast_service",
        payload={"student_id": str(uuid4()), "exam_id": "neet"},
        metadata={},
    )
    with patch(
        "prepos.events.handlers.goal_handlers.request_twin_incremental_update",
        new=AsyncMock(),
    ) as twin_update:
        with patch(
            "prepos.events.handlers.goal_handlers._build_read_service",
            return_value=AsyncMock(),
        ):
            with patch("prepos.events.handlers.goal_handlers.session_scope") as session_scope:
                session_scope.return_value.__aenter__ = AsyncMock(return_value=object())
                session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
                await goal_handlers.on_forecast_updated_twin_projection(envelope)
    assert twin_update.await_args.kwargs["section"] == TwinProjectionSection.FORECAST
