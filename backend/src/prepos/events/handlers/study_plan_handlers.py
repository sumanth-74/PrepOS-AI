from __future__ import annotations

from datetime import datetime
from uuid import UUID

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.study_plan.execution_tracker import StudyPlanExecutionTracker
from prepos.application.study_plan.service import StudyPlanService
from prepos.application.twin.rebuild_factory import build_forecast_service, request_twin_incremental_update
from prepos.core.database import session_scope
from prepos.core.logging import get_logger
from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.domain.study_plan.value_objects import ActivityType
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


def _build_execution_tracker(session: object) -> StudyPlanExecutionTracker:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    return StudyPlanExecutionTracker(
        execution_repo=SqlAlchemyStudyPlanExecutionRepository(session),
        outbox=OutboxPublisher(session),
    )


def _build_study_plan_service(session: object) -> StudyPlanService:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    read_service = _build_read_service(session)
    outbox = OutboxPublisher(session)
    execution_repo = SqlAlchemyStudyPlanExecutionRepository(session)
    forecast_service = build_forecast_service(session=session, read_service=read_service)
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
        forecast_service=forecast_service,
        outbox=outbox,
    )


async def _rebuild_study_plan(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    capacity_raw = payload.get("adaptive_capacity_minutes")
    daily_capacity = int(str(capacity_raw)) if capacity_raw is not None else None
    async with session_scope() as session:
        service = _build_study_plan_service(session)
        await service.rebuild_study_plan(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(payload["exam_id"]),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
            daily_capacity_minutes=daily_capacity,
        )
        logger.info(
            "study_plan_rebuilt",
            student_id=str(payload["student_id"]),
            exam_id=str(payload["exam_id"]),
            correlation_id=envelope.correlation_id,
        )


async def on_learning_graph_updated_study_plan(envelope: DomainEventEnvelope) -> None:
    await _rebuild_study_plan(envelope)


async def on_twin_recommendations_updated_study_plan(envelope: DomainEventEnvelope) -> None:
    await _rebuild_study_plan(envelope)


async def on_revision_queue_updated_study_plan(envelope: DomainEventEnvelope) -> None:
    await _rebuild_study_plan(envelope)


async def on_study_behavior_updated_study_plan(envelope: DomainEventEnvelope) -> None:
    await _rebuild_study_plan(envelope)


async def on_forecast_updated_study_plan(envelope: DomainEventEnvelope) -> None:
    await _rebuild_study_plan(envelope)


async def on_study_plan_item_completed_execution(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        tracker = _build_execution_tracker(session)
        await tracker.handle_item_completed(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(payload["exam_id"]),
            concept_id=str(payload["concept_id"]),
            activity_type=ActivityType(str(payload["activity_type"])),
            planned_minutes=int(str(payload["planned_minutes"])),
            actual_minutes=int(str(payload["actual_minutes"])),
            completed_at=datetime.fromisoformat(str(payload["completed_at"])),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "study_plan_item_completed",
            student_id=str(payload["student_id"]),
            concept_id=str(payload["concept_id"]),
            correlation_id=envelope.correlation_id,
        )


async def on_study_plan_item_skipped_execution(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        tracker = _build_execution_tracker(session)
        await tracker.handle_item_skipped(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(payload["exam_id"]),
            concept_id=str(payload["concept_id"]),
            activity_type=ActivityType(str(payload["activity_type"])),
            planned_minutes=int(str(payload["planned_minutes"])),
            actual_minutes=int(str(payload["actual_minutes"])),
            completed_at=datetime.fromisoformat(str(payload["completed_at"])),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "study_plan_item_skipped",
            student_id=str(payload["student_id"]),
            concept_id=str(payload["concept_id"]),
            correlation_id=envelope.correlation_id,
        )


async def on_study_plan_updated_twin_projection(envelope: DomainEventEnvelope) -> None:
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
            section=TwinProjectionSection.STUDY_PLAN,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


def register_event_handlers() -> None:
    dispatcher.register(
        "LearningGraphUpdated",
        "study_plan_generator",
        on_learning_graph_updated_study_plan,
    )
    dispatcher.register(
        "TwinRecommendationsUpdated",
        "study_plan_generator",
        on_twin_recommendations_updated_study_plan,
    )
    dispatcher.register(
        "RevisionQueueUpdated",
        "study_plan_generator",
        on_revision_queue_updated_study_plan,
    )
    dispatcher.register(
        "StudyBehaviorUpdated",
        "study_plan_generator",
        on_study_behavior_updated_study_plan,
    )
    dispatcher.register(
        "ForecastUpdated",
        "study_plan_generator",
        on_forecast_updated_study_plan,
    )
    dispatcher.register(
        "StudyPlanItemCompleted",
        "study_plan_execution_tracker",
        on_study_plan_item_completed_execution,
    )
    dispatcher.register(
        "StudyPlanItemSkipped",
        "study_plan_execution_tracker",
        on_study_plan_item_skipped_execution,
    )
    dispatcher.register(
        "StudyPlanUpdated",
        "twin_rebuild_orchestrator",
        on_study_plan_updated_twin_projection,
    )


register_event_handlers()
