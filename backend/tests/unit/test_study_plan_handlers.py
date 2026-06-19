from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.events.handlers import study_plan_handlers


@pytest.mark.asyncio
async def test_study_plan_updated_requests_study_plan_projection() -> None:
    envelope = DomainEventEnvelope(
        event_id=uuid4(),
        event_version=1,
        event_type="StudyPlanUpdated",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=uuid4(),
        correlation_id="corr",
        causation_id="cause",
        producer="study_plan_service",
        payload={"student_id": str(uuid4()), "exam_id": "neet"},
        metadata={},
    )
    with patch(
        "prepos.events.handlers.study_plan_handlers.request_twin_incremental_update",
        new=AsyncMock(),
    ) as twin_update:
        with patch(
            "prepos.events.handlers.study_plan_handlers._build_read_service",
            return_value=AsyncMock(),
        ):
            with patch("prepos.events.handlers.study_plan_handlers.session_scope") as session_scope:
                session_scope.return_value.__aenter__ = AsyncMock(return_value=object())
                session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
                await study_plan_handlers.on_study_plan_updated_twin_projection(envelope)
    assert twin_update.await_args.kwargs["section"] == TwinProjectionSection.STUDY_PLAN
