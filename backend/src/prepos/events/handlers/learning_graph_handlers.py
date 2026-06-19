from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from prepos.application.learning_graph.services import LearningGraphService
from prepos.core.database import session_scope
from prepos.core.logging import get_logger
from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.events.dispatcher import dispatcher
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork
from prepos.infrastructure.db.repositories.learning_graph_repository import SqlAlchemyLearningGraphRepository

logger = get_logger(__name__)


async def _build_service(session: object) -> LearningGraphService:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    return LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(session),
        outbox=OutboxPublisher(session),
        cache=NoOpLearningGraphCache(),
    )


async def on_student_onboarding_completed(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    tenant_id = envelope.tenant_id
    student_id = UUID(str(envelope.payload["student_id"]))
    exam_id = str(envelope.payload["exam_id"])
    catalog_version = str(envelope.payload["catalog_version"])

    async with session_scope() as session:
        service = await _build_service(session)
        count = await service.provision_from_onboarding(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            catalog_version=catalog_version,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )
        logger.info(
            "learning_graph_provisioned",
            student_id=str(student_id),
            node_count=count,
            correlation_id=envelope.correlation_id,
        )


async def on_assessment_completed(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        service = await _build_service(session)
        await service.handle_assessment_completed(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            concept_id=str(payload["concept_id"]),
            mcq_correct=bool(payload.get("mcq_correct", payload.get("correct", False))),
            self_confidence=(
                Decimal(str(payload["self_confidence"]))
                if payload.get("self_confidence") is not None
                else None
            ),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


async def on_revision_completed(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        service = await _build_service(session)
        await service.handle_revision_completed(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            concept_id=str(payload["concept_id"]),
            recall_grade=str(payload.get("recall_grade", "good")),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


async def on_study_session_logged(envelope: DomainEventEnvelope) -> None:
    if envelope.tenant_id is None:
        return
    payload = envelope.payload
    async with session_scope() as session:
        service = await _build_service(session)
        await service.handle_study_session_logged(
            tenant_id=envelope.tenant_id,
            student_id=UUID(str(payload["student_id"])),
            concept_id=str(payload["concept_id"]),
            engaged_minutes=int(str(payload.get("engaged_minutes", 0))),
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


async def on_pyq_data_changed(envelope: DomainEventEnvelope) -> None:
    payload = envelope.payload
    concept_id = str(payload["concept_id"])
    global_importance = Decimal(str(payload.get("global_importance", payload.get("importance", 50))))
    tenant_id_raw = payload.get("tenant_id", envelope.tenant_id)
    student_id_raw = payload.get("student_id")
    if tenant_id_raw is None or student_id_raw is None:
        return
    async with session_scope() as session:
        service = await _build_service(session)
        await service.handle_pyq_data_changed(
            tenant_id=UUID(str(tenant_id_raw)),
            student_id=UUID(str(student_id_raw)),
            concept_id=concept_id,
            global_importance=global_importance,
            correlation_id=envelope.correlation_id,
            causation_id=str(envelope.event_id),
        )


def register_event_handlers() -> None:
    dispatcher.register(
        "StudentOnboardingCompleted",
        "learning_graph_provisioner",
        on_student_onboarding_completed,
    )
    dispatcher.register("AssessmentCompleted", "learning_graph_assessment", on_assessment_completed)
    dispatcher.register("RevisionCompleted", "learning_graph_revision", on_revision_completed)
    dispatcher.register("StudySessionLogged", "learning_graph_study", on_study_session_logged)
    dispatcher.register("PYQDataChanged", "learning_graph_pyq", on_pyq_data_changed)


register_event_handlers()
