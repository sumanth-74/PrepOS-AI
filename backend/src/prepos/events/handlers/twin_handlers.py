from __future__ import annotations

from uuid import UUID

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.revision_queue.projector import RevisionQueueProjector
from prepos.application.twin.rebuild_factory import request_twin_incremental_update
from prepos.application.twin.services import TwinRecommendationService
from prepos.core.database import session_scope
from prepos.core.logging import get_logger
from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.events.dispatcher import dispatcher
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.repositories.learning_graph_repository import (
    SqlAlchemyLearningGraphReadRepository,
    SqlAlchemyLearningGraphRepository,
)
from prepos.infrastructure.db.repositories.revision_queue_repository import SqlAlchemyRevisionQueueRepository
from prepos.infrastructure.db.repositories.twin_repository import SqlAlchemyTwinRecommendationRepository

logger = get_logger(__name__)


def _build_read_service(session: object) -> LearningGraphReadService:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    return LearningGraphReadService(
        read_repo=SqlAlchemyLearningGraphReadRepository(session),
        write_repo=SqlAlchemyLearningGraphRepository(session),
        cache=NoOpLearningGraphCache(),
    )


async def on_learning_graph_updated_revision_queue(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        projector = RevisionQueueProjector(
            graph_repo=SqlAlchemyLearningGraphRepository(session),
            queue_repo=SqlAlchemyRevisionQueueRepository(session),
            outbox=OutboxPublisher(session),
        )
        action = await projector.project_concept(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(payload["exam_id"]),
            concept_id=str(payload["concept_id"]),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "revision_queue_projected",
            student_id=str(payload["student_id"]),
            concept_id=str(payload["concept_id"]),
            action=action,
            correlation_id=envelope.correlation_id,
        )


async def on_learning_graph_updated_twin_recommendations(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        service = TwinRecommendationService(
            learning_graph_read_service=_build_read_service(session),
            recommendation_repo=SqlAlchemyTwinRecommendationRepository(session),
            outbox=OutboxPublisher(session),
        )
        await service.recompute_recommendation_for_concept(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(payload["exam_id"]),
            concept_id=str(payload["concept_id"]),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "twin_recommendation_incremental",
            student_id=str(payload["student_id"]),
            concept_id=str(payload["concept_id"]),
            exam_id=str(payload["exam_id"]),
            correlation_id=envelope.correlation_id,
        )


async def on_learning_graph_updated_twin_rebuild(envelope: DomainEventEnvelope) -> None:
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
            section=TwinProjectionSection.READINESS,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
            concept_id=str(payload["concept_id"]),
            learning_graph_row_version=int(str(payload["row_version"])),
        )
        logger.info(
            "twin_readiness_incremental",
            student_id=str(payload["student_id"]),
            exam_id=str(payload["exam_id"]),
            correlation_id=envelope.correlation_id,
        )


async def on_twin_recommendations_updated(envelope: DomainEventEnvelope) -> None:
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
            section=TwinProjectionSection.RECOMMENDATIONS,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


async def on_revision_queue_updated(envelope: DomainEventEnvelope) -> None:
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
            section=TwinProjectionSection.QUEUE,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


def register_event_handlers() -> None:
    dispatcher.register(
        "LearningGraphUpdated",
        "revision_queue_projector",
        on_learning_graph_updated_revision_queue,
    )
    dispatcher.register(
        "LearningGraphUpdated",
        "twin_recommendation_engine",
        on_learning_graph_updated_twin_recommendations,
    )
    dispatcher.register(
        "LearningGraphUpdated",
        "twin_rebuild_orchestrator",
        on_learning_graph_updated_twin_rebuild,
    )
    dispatcher.register(
        "TwinRecommendationsUpdated",
        "twin_rebuild_orchestrator",
        on_twin_recommendations_updated,
    )
    dispatcher.register(
        "RevisionQueueUpdated",
        "twin_rebuild_orchestrator",
        on_revision_queue_updated,
    )


register_event_handlers()
