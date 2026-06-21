from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class DomainEventType(StrEnum):
    RECOMMENDATION_COMPLETED = "RecommendationCompleted"
    READINESS_CHANGED = "ReadinessChanged"
    FORECAST_UPDATED = "ForecastUpdated"
    INTERVENTION_COMPLETED = "InterventionCompleted"
    PLAN_GENERATED = "PlanGenerated"
    MEMORY_CREATED = "MemoryCreated"


@dataclass(frozen=True)
class DomainEvent:
    event_type: DomainEventType
    tenant_id: UUID | None
    payload: dict[str, object] = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
