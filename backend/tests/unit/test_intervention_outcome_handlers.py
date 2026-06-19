from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.events.handlers import intervention_outcome_handlers


@pytest.mark.asyncio
async def test_intervention_optimization_updated_requests_projection() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    envelope = DomainEventEnvelope(
        event_id=uuid4(),
        event_version=1,
        event_type="InterventionOptimizationUpdated",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=tenant_id,
        correlation_id="corr",
        causation_id="cause",
        producer="intervention_optimization_service",
        payload={
            "student_id": str(student_id),
            "exam_id": "neet",
        },
        metadata={},
    )

    with patch(
        "prepos.events.handlers.intervention_outcome_handlers.request_twin_incremental_update",
        new=AsyncMock(),
    ) as twin_update:
        with patch(
            "prepos.events.handlers.intervention_outcome_handlers._build_read_service",
            return_value=AsyncMock(),
        ):
            with patch("prepos.events.handlers.intervention_outcome_handlers.session_scope") as session_scope:
                session_scope.return_value.__aenter__ = AsyncMock(return_value=object())
                session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
                await intervention_outcome_handlers.on_intervention_optimization_updated_projection(envelope)

    twin_update.assert_awaited_once()
    assert twin_update.await_args.kwargs["section"] == TwinProjectionSection.INTERVENTION_OUTCOME
