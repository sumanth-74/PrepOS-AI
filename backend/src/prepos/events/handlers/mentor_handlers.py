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


async def _publish_mentor_insights(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    exam_id = payload.get("exam_id")
    if exam_id is None:
        return
    async with session_scope() as session:
        service = build_mentor_service(session=session)
        await service.publish_mentor_insight_updated(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(exam_id),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "mentor_insight_published",
            student_id=str(payload["student_id"]),
            exam_id=str(exam_id),
            correlation_id=envelope.correlation_id,
        )


async def on_learning_graph_updated_mentor(envelope: DomainEventEnvelope) -> None:
    await _publish_mentor_insights(envelope)


async def on_forecast_updated_mentor(envelope: DomainEventEnvelope) -> None:
    await _publish_mentor_insights(envelope)


async def on_milestone_updated_mentor(envelope: DomainEventEnvelope) -> None:
    await _publish_mentor_insights(envelope)


async def on_personalization_updated_mentor(envelope: DomainEventEnvelope) -> None:
    await _publish_mentor_insights(envelope)


async def on_intervention_optimization_updated_mentor(envelope: DomainEventEnvelope) -> None:
    await _publish_mentor_insights(envelope)


async def on_mentor_insight_updated_summary(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        service = build_mentor_service(session=session)
        await service.publish_mentor_summary_updated(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(payload["exam_id"]),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


async def on_mentor_summary_updated_projection(envelope: DomainEventEnvelope) -> None:
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
            section=TwinProjectionSection.MENTOR,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


def register_event_handlers() -> None:
    dispatcher.register(
        "LearningGraphUpdated",
        "mentor_insight_engine",
        on_learning_graph_updated_mentor,
    )
    dispatcher.register(
        "ForecastUpdated",
        "mentor_insight_engine",
        on_forecast_updated_mentor,
    )
    dispatcher.register(
        "MilestoneUpdated",
        "mentor_insight_engine",
        on_milestone_updated_mentor,
    )
    dispatcher.register(
        "PersonalizationUpdated",
        "mentor_insight_engine",
        on_personalization_updated_mentor,
    )
    dispatcher.register(
        "InterventionOptimizationUpdated",
        "mentor_insight_engine",
        on_intervention_optimization_updated_mentor,
    )
    dispatcher.register(
        "MentorInsightUpdated",
        "mentor_summary_engine",
        on_mentor_insight_updated_summary,
    )
    dispatcher.register(
        "MentorSummaryUpdated",
        "twin_rebuild_orchestrator",
        on_mentor_summary_updated_projection,
    )


register_event_handlers()
