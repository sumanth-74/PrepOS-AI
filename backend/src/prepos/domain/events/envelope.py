from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DomainEventEnvelope:
    event_id: UUID
    event_version: int
    event_type: str
    occurred_at: datetime
    recorded_at: datetime
    tenant_id: UUID | None
    correlation_id: str
    causation_id: str | None
    producer: str
    payload: dict[str, object]
    metadata: dict[str, object] | None = None
