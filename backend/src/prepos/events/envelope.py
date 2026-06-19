from __future__ import annotations

from typing import Any

from prepos.domain.events.envelope import DomainEventEnvelope


def envelope_to_dict(envelope: DomainEventEnvelope) -> dict[str, Any]:
    return {
        "event_id": str(envelope.event_id),
        "event_version": envelope.event_version,
        "event_type": envelope.event_type,
        "occurred_at": envelope.occurred_at.isoformat(),
        "recorded_at": envelope.recorded_at.isoformat(),
        "tenant_id": str(envelope.tenant_id) if envelope.tenant_id else None,
        "correlation_id": envelope.correlation_id,
        "causation_id": envelope.causation_id,
        "producer": envelope.producer,
        "payload": envelope.payload,
        "metadata": envelope.metadata,
    }


def envelope_from_dict(data: dict[str, Any]) -> DomainEventEnvelope:
    from datetime import datetime
    from uuid import UUID

    tenant_raw = data.get("tenant_id")
    return DomainEventEnvelope(
        event_id=UUID(str(data["event_id"])),
        event_version=int(data["event_version"]),
        event_type=str(data["event_type"]),
        occurred_at=datetime.fromisoformat(str(data["occurred_at"]).replace("Z", "+00:00")),
        recorded_at=datetime.fromisoformat(str(data["recorded_at"]).replace("Z", "+00:00")),
        tenant_id=UUID(str(tenant_raw)) if tenant_raw else None,
        correlation_id=str(data["correlation_id"]),
        causation_id=str(data["causation_id"]) if data.get("causation_id") else None,
        producer=str(data["producer"]),
        payload=dict(data.get("payload") or {}),
        metadata=dict(data["metadata"]) if data.get("metadata") else None,
    )
