from __future__ import annotations

from uuid import UUID

from prepos.application.goal.forecast_service import ForecastService
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.twin.rebuild_factory import (
    build_forecast_service,
    request_twin_incremental_update,
)
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


def _build_forecast_service(session: object, read_service: LearningGraphReadService) -> ForecastService:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    return build_forecast_service(session=session, read_service=read_service)


async def on_goal_updated_forecast(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        read_service = _build_read_service(session)
        forecast_service = _build_forecast_service(session, read_service)
        await forecast_service.publish_forecast_updated(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(payload["exam_id"]),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "forecast_published_after_goal_update",
            student_id=str(payload["student_id"]),
            exam_id=str(payload["exam_id"]),
            correlation_id=envelope.correlation_id,
        )


async def on_learning_graph_updated_forecast(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    exam_id = payload.get("exam_id")
    if exam_id is None:
        return
    async with session_scope() as session:
        read_service = _build_read_service(session)
        forecast_service = _build_forecast_service(session, read_service)
        await forecast_service.publish_forecast_updated(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(exam_id),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "forecast_published_after_learning_graph_update",
            student_id=str(payload["student_id"]),
            exam_id=str(exam_id),
            correlation_id=envelope.correlation_id,
        )


async def on_forecast_updated_twin_projection(envelope: DomainEventEnvelope) -> None:
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
            section=TwinProjectionSection.FORECAST,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


def register_event_handlers() -> None:
    dispatcher.register(
        "GoalUpdated",
        "forecast_engine",
        on_goal_updated_forecast,
    )
    dispatcher.register(
        "LearningGraphUpdated",
        "forecast_engine",
        on_learning_graph_updated_forecast,
    )
    dispatcher.register(
        "ForecastUpdated",
        "twin_rebuild_orchestrator",
        on_forecast_updated_twin_projection,
    )


register_event_handlers()
