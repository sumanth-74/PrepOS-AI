from __future__ import annotations

from prepos.core.logging import get_logger
from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.events.dispatcher import dispatcher

logger = get_logger(__name__)


async def on_domain_catalog_updated(envelope: DomainEventEnvelope) -> None:
    logger.info(
        "domain_catalog_updated_received",
        exam_id=envelope.payload.get("exam_id"),
        catalog_version=envelope.payload.get("catalog_version"),
        concepts_added=len(envelope.payload.get("concepts_added", [])),  # type: ignore[arg-type]
        concepts_deprecated=len(envelope.payload.get("concepts_deprecated", [])),  # type: ignore[arg-type]
        correlation_id=envelope.correlation_id,
    )


def register_event_handlers() -> None:
    dispatcher.register("DomainCatalogUpdated", "exam_catalog_consumer", on_domain_catalog_updated)


register_event_handlers()
