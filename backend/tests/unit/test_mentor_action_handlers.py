from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.events.handlers import mentor_action_handlers


@pytest.mark.asyncio
async def test_escalation_updated_requests_mentor_action_projection() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    envelope = DomainEventEnvelope(
        event_id=uuid4(),
        event_version=1,
        event_type="EscalationUpdated",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=tenant_id,
        correlation_id="corr",
        causation_id="cause",
        producer="mentor_service",
        payload={
            "student_id": str(student_id),
            "exam_id": "neet",
        },
        metadata={},
    )

    with patch(
        "prepos.events.handlers.mentor_action_handlers.request_twin_incremental_update",
        new=AsyncMock(),
    ) as twin_update:
        with patch(
            "prepos.events.handlers.mentor_action_handlers._build_read_service",
            return_value=AsyncMock(),
        ):
            with patch("prepos.events.handlers.mentor_action_handlers.session_scope") as session_scope:
                session_scope.return_value.__aenter__ = AsyncMock(return_value=object())
                session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
                await mentor_action_handlers.on_escalation_updated_projection(envelope)

    twin_update.assert_awaited_once()
    assert twin_update.await_args.kwargs["section"] == TwinProjectionSection.MENTOR_ACTION


@pytest.mark.asyncio
async def test_mentor_insight_updated_publishes_mentor_action() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    envelope = DomainEventEnvelope(
        event_id=uuid4(),
        event_version=1,
        event_type="MentorInsightUpdated",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=tenant_id,
        correlation_id="corr",
        causation_id="cause",
        producer="mentor_service",
        payload={
            "student_id": str(student_id),
            "exam_id": "neet",
        },
        metadata={},
    )

    with patch(
        "prepos.events.handlers.mentor_action_handlers.build_mentor_service",
    ) as build_service:
        service = AsyncMock()
        service.publish_mentor_action_updated = AsyncMock()
        build_service.return_value = service
        with patch("prepos.events.handlers.mentor_action_handlers.session_scope") as session_scope:
            session_scope.return_value.__aenter__ = AsyncMock(return_value=object())
            session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
            await mentor_action_handlers.on_mentor_insight_updated_action(envelope)

    service.publish_mentor_action_updated.assert_awaited_once()
