from __future__ import annotations

from prepos.core.logging import get_logger
from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.events.dispatcher import dispatcher

logger = get_logger(__name__)


async def on_student_registered(envelope: DomainEventEnvelope) -> None:
    logger.info(
        "student_registered_received",
        tenant_id=str(envelope.tenant_id),
        user_id=envelope.payload.get("user_id"),
        correlation_id=envelope.correlation_id,
    )


def register_event_handlers() -> None:
    dispatcher.register("StudentRegistered", "foundation_consumer", on_student_registered)


register_event_handlers()
