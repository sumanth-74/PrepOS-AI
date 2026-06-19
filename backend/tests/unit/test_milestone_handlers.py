from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.events.handlers import milestone_handlers


@pytest.mark.asyncio
async def test_milestone_updated_requests_twin_projection() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    envelope = DomainEventEnvelope(
        event_id=uuid4(),
        event_version=1,
        event_type="MilestoneUpdated",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=tenant_id,
        correlation_id="corr",
        causation_id="cause",
        producer="milestone_service",
        payload={
            "student_id": str(student_id),
            "exam_id": "neet",
        },
        metadata={},
    )

    with patch(
        "prepos.events.handlers.milestone_handlers.request_twin_incremental_update",
        new=AsyncMock(),
    ) as twin_update:
        with patch(
            "prepos.events.handlers.milestone_handlers._build_read_service",
            return_value=AsyncMock(),
        ):
            with patch("prepos.events.handlers.milestone_handlers.session_scope") as session_scope:
                session_scope.return_value.__aenter__ = AsyncMock(return_value=object())
                session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
                await milestone_handlers.on_milestone_updated_twin_projection(envelope)

    twin_update.assert_awaited_once()
    assert twin_update.await_args.kwargs["section"] == TwinProjectionSection.MILESTONES
