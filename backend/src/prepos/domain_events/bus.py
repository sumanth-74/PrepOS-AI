from __future__ import annotations

from abc import ABC, abstractmethod

from prepos.domain_events.events import DomainEvent


class EventBusPort(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> str: ...


class InMemoryEventBus(EventBusPort):
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> str:
        self.published.append(event)
        return str(event.event_id)
