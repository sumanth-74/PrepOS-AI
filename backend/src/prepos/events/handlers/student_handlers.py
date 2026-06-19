from __future__ import annotations

from prepos.core.logging import get_logger
from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.events.dispatcher import dispatcher

logger = get_logger(__name__)


async def on_student_onboarding_completed(envelope: DomainEventEnvelope) -> None:
    logger.info(
        "student_onboarding_completed_received",
        student_id=envelope.payload.get("student_id"),
        exam_id=envelope.payload.get("exam_id"),
        target_stages=envelope.payload.get("target_stages"),
        diagnostic_offered=envelope.payload.get("diagnostic_offered"),
        correlation_id=envelope.correlation_id,
    )


def register_event_handlers() -> None:
    dispatcher.register(
        "StudentOnboardingCompleted",
        "student_onboarding_consumer",
        on_student_onboarding_completed,
    )


register_event_handlers()
