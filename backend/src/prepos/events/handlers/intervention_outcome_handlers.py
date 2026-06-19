from __future__ import annotations

from uuid import UUID

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.twin.rebuild_factory import (
    build_intervention_optimization_service,
    build_intervention_outcome_service,
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


async def _calculate_intervention_outcome(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    exam_id = payload.get("exam_id")
    if exam_id is None:
        return
    async with session_scope() as session:
        read_service = _build_read_service(session)
        service = build_intervention_outcome_service(session=session, read_service=read_service)
        await service.publish_intervention_outcome_calculated(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(exam_id),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "intervention_outcome_calculated",
            student_id=str(payload["student_id"]),
            exam_id=str(exam_id),
            correlation_id=envelope.correlation_id,
        )


async def on_study_behavior_updated_intervention_outcome(envelope: DomainEventEnvelope) -> None:
    await _calculate_intervention_outcome(envelope)


async def on_forecast_updated_intervention_outcome(envelope: DomainEventEnvelope) -> None:
    await _calculate_intervention_outcome(envelope)


async def on_predicted_score_updated_intervention_outcome(envelope: DomainEventEnvelope) -> None:
    await _calculate_intervention_outcome(envelope)


async def on_intervention_outcome_calculated_optimization(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        service = build_intervention_optimization_service(session=session)
        await service.publish_intervention_optimization_updated(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(payload["exam_id"]),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


async def on_intervention_optimization_updated_projection(envelope: DomainEventEnvelope) -> None:
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
            section=TwinProjectionSection.INTERVENTION_OUTCOME,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


def register_event_handlers() -> None:
    dispatcher.register(
        "StudyBehaviorUpdated",
        "intervention_outcome_engine",
        on_study_behavior_updated_intervention_outcome,
    )
    dispatcher.register(
        "ForecastUpdated",
        "intervention_outcome_engine",
        on_forecast_updated_intervention_outcome,
    )
    dispatcher.register(
        "PredictedScoreUpdated",
        "intervention_outcome_engine",
        on_predicted_score_updated_intervention_outcome,
    )
    dispatcher.register(
        "InterventionOutcomeCalculated",
        "intervention_optimization_engine",
        on_intervention_outcome_calculated_optimization,
    )
    dispatcher.register(
        "InterventionOptimizationUpdated",
        "twin_rebuild_orchestrator",
        on_intervention_optimization_updated_projection,
    )


register_event_handlers()
