from __future__ import annotations

from uuid import UUID

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.study_plan.execution_tracker import StudyPlanExecutionTracker
from prepos.application.study_plan.service import StudyPlanService
from prepos.application.twin.rebuild_factory import (
    build_forecast_service,
    build_personalization_service,
    build_twin_decision_service,
    build_twin_intervention_service,
    request_twin_incremental_update,
)
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
from prepos.infrastructure.db.repositories.study_plan_execution_repository import (
    SqlAlchemyStudyPlanExecutionRepository,
)
from prepos.infrastructure.db.repositories.study_plan_repository import SqlAlchemyStudyPlanRepository
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


async def _publish_personalization(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    exam_id = payload.get("exam_id")
    if exam_id is None:
        return
    async with session_scope() as session:
        service = build_personalization_service(session=session)
        await service.publish_personalization_updated(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(exam_id),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "personalization_published",
            student_id=str(payload["student_id"]),
            exam_id=str(exam_id),
            correlation_id=envelope.correlation_id,
        )


async def on_behavior_profile_updated_personalization(envelope: DomainEventEnvelope) -> None:
    await _publish_personalization(envelope)


async def on_intervention_optimization_updated_personalization(envelope: DomainEventEnvelope) -> None:
    await _publish_personalization(envelope)


async def on_intervention_outcome_calculated_personalization(envelope: DomainEventEnvelope) -> None:
    await _publish_personalization(envelope)


def _build_study_plan_service(session: object) -> StudyPlanService:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    read_service = _build_read_service(session)
    outbox = OutboxPublisher(session)
    execution_repo = SqlAlchemyStudyPlanExecutionRepository(session)
    return StudyPlanService(
        read_service=read_service,
        recommendation_repo=SqlAlchemyTwinRecommendationRepository(session),
        queue_repo=SqlAlchemyRevisionQueueRepository(session),
        study_plan_repo=SqlAlchemyStudyPlanRepository(session),
        execution_repo=execution_repo,
        execution_tracker=StudyPlanExecutionTracker(
            execution_repo=execution_repo,
            outbox=outbox,
        ),
        forecast_service=build_forecast_service(session=session, read_service=read_service),
        outbox=outbox,
        personalization_service=build_personalization_service(session=session),
    )


async def on_personalization_updated_rebuild(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    exam_id = str(payload["exam_id"])
    student_id = UUID(str(payload["student_id"]))
    async with session_scope() as session:
        read_service = _build_read_service(session)
        personalization_service = build_personalization_service(session=session)
        recommendation_service = TwinRecommendationService(
            learning_graph_read_service=read_service,
            recommendation_repo=SqlAlchemyTwinRecommendationRepository(session),
            outbox=OutboxPublisher(session),
            personalization_service=personalization_service,
        )
        await recommendation_service.recompute_and_persist(
            tenant_id=envelope.tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        decision_service = build_twin_decision_service(session=session, read_service=read_service)
        await decision_service.publish_twin_decision_updated(
            tenant_id=envelope.tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        intervention_service = build_twin_intervention_service(session=session, read_service=read_service)
        await intervention_service.publish_twin_intervention_updated(
            tenant_id=envelope.tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        study_plan_service = _build_study_plan_service(session)
        await study_plan_service.rebuild_study_plan(
            tenant_id=envelope.tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        await request_twin_incremental_update(
            session=session,
            read_service=read_service,
            tenant_id=envelope.tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            section=TwinProjectionSection.PERSONALIZATION,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


def register_event_handlers() -> None:
    dispatcher.register(
        "BehaviorProfileUpdated",
        "personalization_engine",
        on_behavior_profile_updated_personalization,
    )
    dispatcher.register(
        "InterventionOptimizationUpdated",
        "personalization_engine",
        on_intervention_optimization_updated_personalization,
    )
    dispatcher.register(
        "InterventionOutcomeCalculated",
        "personalization_engine",
        on_intervention_outcome_calculated_personalization,
    )
    dispatcher.register(
        "PersonalizationUpdated",
        "personalized_rebuild_orchestrator",
        on_personalization_updated_rebuild,
    )


register_event_handlers()
