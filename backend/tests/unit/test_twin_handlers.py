from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.events.handlers import twin_handlers


def _envelope(*, event_type: str) -> DomainEventEnvelope:
    return DomainEventEnvelope(
        event_id=uuid4(),
        event_version=1,
        event_type=event_type,
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=uuid4(),
        correlation_id="corr",
        causation_id="cause",
        producer="test",
        payload={
            "student_id": str(uuid4()),
            "exam_id": "neet",
            "concept_id": "concept-a",
            "row_version": 2,
        },
        metadata={},
    )


@pytest.mark.asyncio
async def test_learning_graph_updated_requests_readiness_projection() -> None:
    with patch(
        "prepos.events.handlers.twin_handlers.request_twin_incremental_update",
        new=AsyncMock(),
    ) as twin_update:
        with patch(
            "prepos.events.handlers.twin_handlers._build_read_service",
            return_value=AsyncMock(),
        ):
            with patch("prepos.events.handlers.twin_handlers.session_scope") as session_scope:
                session_scope.return_value.__aenter__ = AsyncMock(return_value=object())
                session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
                await twin_handlers.on_learning_graph_updated_twin_rebuild(
                    _envelope(event_type="LearningGraphUpdated")
                )
    assert twin_update.await_args.kwargs["section"] == TwinProjectionSection.READINESS


@pytest.mark.asyncio
async def test_twin_recommendations_updated_requests_recommendations_projection() -> None:
    with patch(
        "prepos.events.handlers.twin_handlers.request_twin_incremental_update",
        new=AsyncMock(),
    ) as twin_update:
        with patch(
            "prepos.events.handlers.twin_handlers._build_read_service",
            return_value=AsyncMock(),
        ):
            with patch("prepos.events.handlers.twin_handlers.session_scope") as session_scope:
                session_scope.return_value.__aenter__ = AsyncMock(return_value=object())
                session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
                await twin_handlers.on_twin_recommendations_updated(
                    _envelope(event_type="TwinRecommendationsUpdated")
                )
    assert twin_update.await_args.kwargs["section"] == TwinProjectionSection.RECOMMENDATIONS


@pytest.mark.asyncio
async def test_revision_queue_updated_requests_queue_projection() -> None:
    with patch(
        "prepos.events.handlers.twin_handlers.request_twin_incremental_update",
        new=AsyncMock(),
    ) as twin_update:
        with patch(
            "prepos.events.handlers.twin_handlers._build_read_service",
            return_value=AsyncMock(),
        ):
            with patch("prepos.events.handlers.twin_handlers.session_scope") as session_scope:
                session_scope.return_value.__aenter__ = AsyncMock(return_value=object())
                session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
                await twin_handlers.on_revision_queue_updated(
                    _envelope(event_type="RevisionQueueUpdated")
                )
    assert twin_update.await_args.kwargs["section"] == TwinProjectionSection.QUEUE
