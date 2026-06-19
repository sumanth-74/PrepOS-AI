from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.events.envelope import envelope_from_dict, envelope_to_dict
from prepos.infrastructure.db.repositories.event_repository import ProcessedEventRepository


@pytest.mark.asyncio
async def test_processed_event_idempotency(db_session) -> None:
    repo = ProcessedEventRepository(db_session)
    envelope = DomainEventEnvelope(
        event_id=uuid4(),
        event_version=1,
        event_type="StudentRegistered",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=uuid4(),
        correlation_id="corr-1",
        causation_id=None,
        producer="auth_service",
        payload={"user_id": str(uuid4())},
    )
    first = await repo.try_claim(consumer_name="foundation_consumer", envelope=envelope)
    await db_session.commit()
    second = await repo.try_claim(consumer_name="foundation_consumer", envelope=envelope)
    assert first is True
    assert second is False


def test_envelope_roundtrip() -> None:
    envelope = DomainEventEnvelope(
        event_id=uuid4(),
        event_version=1,
        event_type="StudentRegistered",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=uuid4(),
        correlation_id="corr-1",
        causation_id=None,
        producer="auth_service",
        payload={"user_id": str(uuid4())},
        metadata={"scope": "tenant"},
    )
    restored = envelope_from_dict(envelope_to_dict(envelope))
    assert restored.event_id == envelope.event_id
    assert restored.event_type == envelope.event_type
