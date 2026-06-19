from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from test_learning_graph_event_handlers import _provision_graph_for_student

from prepos.domain.learning_graph.events import RevisionCompleted
from prepos.events.dispatcher import dispatcher
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.db.repositories.event_repository import OutboxRepository


async def _dispatch_revision_completed_event(
    db_session: AsyncSession,
    *,
    tenant_id: UUID,
    student_id: UUID,
    exam_id: str,
    concept_id: str,
    correlation_id: str,
) -> None:
    outbox = OutboxPublisher(db_session)
    await outbox.enqueue_revision_completed(
        RevisionCompleted(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            concept_id=concept_id,
            recall_grade="good",
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=datetime.now(UTC),
        )
    )
    await db_session.commit()
    event = next(
        item
        for item in await OutboxRepository(db_session).fetch_pending(limit=50)
        if item.event_type == "RevisionCompleted" and item.correlation_id == correlation_id
    )
    await dispatcher.dispatch(event)
    await db_session.commit()


@pytest.mark.asyncio
async def test_revision_completed_event_triggers_learning_graph_update(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    correlation_id = "i11-lg-cascade"
    await _dispatch_revision_completed_event(
        db_session,
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        exam_id="upsc_cse",
        concept_id=concept_id,
        correlation_id=correlation_id,
    )
    pending = await OutboxRepository(db_session).fetch_pending(limit=200)
    lg_events = [
        event
        for event in pending
        if event.event_type == "LearningGraphUpdated" and event.correlation_id == correlation_id
    ]
    assert lg_events, "RevisionCompleted handler should emit LearningGraphUpdated"
