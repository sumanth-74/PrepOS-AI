from __future__ import annotations

from uuid import UUID

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.twin.rebuild_factory import build_mentor_service, request_twin_incremental_update
from prepos.core.database import session_scope
from prepos.core.logging import get_logger
from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.events.dispatcher import dispatcher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.repositories.learning_graph_repository import (
    SqlAlchemyLearningGraphReadRepository,
    SqlAlchemyLearningGraphRepository,
)

logger = get_logger(__name__)


def _build_read_service(session: object) -> LearningGraphReadService:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    return LearningGraphReadService(
        read_repo=SqlAlchemyLearningGraphReadRepository(session),
        write_repo=SqlAlchemyLearningGraphRepository(session),
        cache=NoOpLearningGraphCache(),
    )


async def _publish_mentor_action(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    exam_id = payload.get("exam_id")
    if exam_id is None:
        return
    async with session_scope() as session:
        service = build_mentor_service(session=session)
        await service.publish_mentor_action_updated(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(exam_id),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "mentor_action_published",
            student_id=str(payload["student_id"]),
            exam_id=str(exam_id),
            correlation_id=envelope.correlation_id,
        )


async def on_mentor_insight_updated_action(envelope: DomainEventEnvelope) -> None:
    await _publish_mentor_action(envelope)


async def on_behavior_profile_updated_action(envelope: DomainEventEnvelope) -> None:
    await _publish_mentor_action(envelope)


async def on_forecast_probability_updated_action(envelope: DomainEventEnvelope) -> None:
    await _publish_mentor_action(envelope)


async def on_milestone_updated_action(envelope: DomainEventEnvelope) -> None:
    await _publish_mentor_action(envelope)


async def on_mentor_action_updated_escalation(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        service = build_mentor_service(session=session)
        await service.publish_escalation_updated(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(payload["exam_id"]),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


async def on_escalation_updated_projection(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        await request_twin_incremental_update(
            session=session,
            read_service=_build_read_service(session),
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(payload["exam_id"]),
            section=TwinProjectionSection.MENTOR_ACTION,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


def register_event_handlers() -> None:
    dispatcher.register(
        "MentorInsightUpdated",
        "mentor_action_engine",
        on_mentor_insight_updated_action,
    )
    dispatcher.register(
        "BehaviorProfileUpdated",
        "mentor_action_engine",
        on_behavior_profile_updated_action,
    )
    dispatcher.register(
        "ForecastProbabilityUpdated",
        "mentor_action_engine",
        on_forecast_probability_updated_action,
    )
    dispatcher.register(
        "MilestoneUpdated",
        "mentor_action_engine",
        on_milestone_updated_action,
    )
    dispatcher.register(
        "MentorActionUpdated",
        "escalation_engine",
        on_mentor_action_updated_escalation,
    )
    dispatcher.register(
        "EscalationUpdated",
        "twin_rebuild_orchestrator",
        on_escalation_updated_projection,
    )


register_event_handlers()
