from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DomainCatalogUpdated:
    exam_id: str
    catalog_version: str
    concepts_added: tuple[str, ...]
    concepts_deprecated: tuple[str, ...]
    occurred_at: datetime
    correlation_id: str
    causation_id: str | None = None
    actor_user_id: UUID | None = None

    @property
    def event_type(self) -> str:
        return "DomainCatalogUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "exam_id": self.exam_id,
            "catalog_version": self.catalog_version,
            "concepts_added": list(self.concepts_added),
            "concepts_deprecated": list(self.concepts_deprecated),
        }
