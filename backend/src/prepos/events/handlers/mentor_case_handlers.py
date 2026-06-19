from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.twin.rebuild_factory import (
    build_mentor_case_service,
    request_twin_incremental_update,
)
from prepos.core.database import session_scope
from prepos.core.logging import get_logger
from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.domain.mentor.mentor_types_v1 import ActionUrgency, MentorActionType
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


async def _request_case_projection(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    exam_id = payload.get("exam_id")
    if exam_id is None:
        return
    async with session_scope() as session:
        await request_twin_incremental_update(
            session=session,
            read_service=_build_read_service(session),
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(exam_id),
            section=TwinProjectionSection.MENTOR_CASE,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


async def on_mentor_action_updated_case(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    exam_id = payload.get("exam_id")
    action_type_raw = payload.get("action_type")
    if exam_id is None or action_type_raw is None:
        return
    async with session_scope() as session:
        service = build_mentor_case_service(session=session)
        await service.process_mentor_action_updated(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            exam_id=str(exam_id),
            action_type=MentorActionType(str(action_type_raw)),
            priority_score=Decimal(str(payload.get("priority_score", "0"))),
            urgency=ActionUrgency(str(payload.get("urgency", ActionUrgency.MEDIUM.value))),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "mentor_case_processed",
            student_id=str(payload["student_id"]),
            exam_id=str(exam_id),
            action_type=str(action_type_raw),
            correlation_id=envelope.correlation_id,
        )


async def on_mentor_case_created_projection(envelope: DomainEventEnvelope) -> None:
    await _request_case_projection(envelope)


async def on_mentor_case_updated_projection(envelope: DomainEventEnvelope) -> None:
    await _request_case_projection(envelope)


async def on_mentor_case_resolved_projection(envelope: DomainEventEnvelope) -> None:
    await _request_case_projection(envelope)


def register_event_handlers() -> None:
    dispatcher.register(
        "MentorActionUpdated",
        "mentor_case_engine",
        on_mentor_action_updated_case,
    )
    dispatcher.register(
        "MentorCaseCreated",
        "twin_rebuild_orchestrator",
        on_mentor_case_created_projection,
    )
    dispatcher.register(
        "MentorCaseUpdated",
        "twin_rebuild_orchestrator",
        on_mentor_case_updated_projection,
    )
    dispatcher.register(
        "MentorCaseResolved",
        "twin_rebuild_orchestrator",
        on_mentor_case_resolved_projection,
    )


register_event_handlers()
