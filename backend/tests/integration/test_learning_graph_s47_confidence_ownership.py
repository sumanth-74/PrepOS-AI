from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from test_learning_graph_event_handlers import _provision_graph_for_student

from prepos.application.learning_graph.services import LearningGraphService
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.scoring.confidence_v1 import CONFIDENCE_V1
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.models.learning_graph import ScoreAuditLogModel, StudentConceptProgressModel
from prepos.infrastructure.db.repositories.event_repository import OutboxRepository
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork
from prepos.infrastructure.db.repositories.learning_graph_repository import SqlAlchemyLearningGraphRepository


def _build_service(db_session: AsyncSession) -> LearningGraphService:
    return LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(db_session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(db_session),
        outbox=OutboxPublisher(db_session),
        cache=NoOpLearningGraphCache(),
    )


async def _load_node(
    db_session: AsyncSession,
    *,
    student_id: str,
    concept_id: str,
) -> StudentConceptProgressModel:
    return (
        await db_session.execute(
            select(StudentConceptProgressModel).where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id == concept_id,
            )
        )
    ).scalar_one()


async def _confidence_audit_count(
    db_session: AsyncSession,
    *,
    student_id: str,
    concept_id: str,
) -> int:
    return int(
        (
            await db_session.execute(
                select(func.count())
                .select_from(ScoreAuditLogModel)
                .where(
                    ScoreAuditLogModel.student_id == UUID(student_id),
                    ScoreAuditLogModel.concept_id == concept_id,
                    ScoreAuditLogModel.score_type == "confidence",
                )
            )
        ).scalar_one()
    )


@pytest.mark.asyncio
async def test_study_session_does_not_materialize_confidence(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    updated = await service.handle_study_session_logged(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        engaged_minutes=30,
        correlation_id="s47-study-corr",
        causation_id="s47-study-cause",
    )
    await db_session.commit()

    assert updated.confidence_score is None
    assert updated.confidence_version == CONFIDENCE_V1
    assert updated.node_state == NodeStatus.RATED
    assert await _confidence_audit_count(db_session, student_id=student_id, concept_id=concept_id) == 0


@pytest.mark.asyncio
async def test_revision_does_not_materialize_confidence(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    updated = await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s47-revision-corr",
        causation_id="s47-revision-cause",
    )
    await db_session.commit()

    assert updated.confidence_score is None
    assert updated.confidence_version == CONFIDENCE_V1
    assert updated.node_state == NodeStatus.RATED
    assert await _confidence_audit_count(db_session, student_id=student_id, concept_id=concept_id) == 0


@pytest.mark.asyncio
async def test_pyq_change_does_not_materialize_confidence(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    updated = await service.handle_pyq_data_changed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        global_importance=Decimal("72.50"),
        correlation_id="s47-pyq-corr",
        causation_id="s47-pyq-cause",
    )
    await db_session.commit()

    assert updated.confidence_score is None
    assert updated.confidence_version == CONFIDENCE_V1
    assert updated.importance_score == Decimal("72.50")
    assert await _confidence_audit_count(db_session, student_id=student_id, concept_id=concept_id) == 0


@pytest.mark.asyncio
async def test_assessment_materializes_confidence(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    updated = await service.handle_assessment_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        mcq_correct=True,
        self_confidence=None,
        correlation_id="s47-assessment-corr",
        causation_id="s47-assessment-cause",
    )
    await db_session.commit()

    assert updated.confidence_score is not None
    assert updated.confidence_score == Decimal("55.56")
    assert updated.confidence_version == CONFIDENCE_V1
    assert await _confidence_audit_count(db_session, student_id=student_id, concept_id=concept_id) == 1


@pytest.mark.asyncio
async def test_confidence_ownership_end_to_end_regression(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    provisioned = await _load_node(db_session, student_id=student_id, concept_id=concept_id)
    assert provisioned.node_state == NodeStatus.UNRATED
    assert provisioned.confidence_score is None
    assert provisioned.row_version == 1

    after_study = await service.handle_study_session_logged(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        engaged_minutes=20,
        correlation_id="s47-e2e-study",
        causation_id="s47-e2e-study",
    )
    assert after_study.confidence_score is None
    assert after_study.row_version == 2

    after_revision = await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s47-e2e-revision",
        causation_id="s47-e2e-revision",
    )
    assert after_revision.confidence_score is None
    assert after_revision.row_version == 3

    after_pyq = await service.handle_pyq_data_changed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        global_importance=Decimal("65.00"),
        correlation_id="s47-e2e-pyq",
        causation_id="s47-e2e-pyq",
    )
    assert after_pyq.confidence_score is None
    assert after_pyq.row_version == 4

    after_assessment = await service.handle_assessment_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        mcq_correct=True,
        self_confidence=None,
        correlation_id="s47-e2e-assessment",
        causation_id="s47-e2e-assessment",
    )
    await db_session.commit()

    assert after_assessment.confidence_score is not None
    assert after_assessment.row_version == 5
    assert await _confidence_audit_count(db_session, student_id=student_id, concept_id=concept_id) == 1

    outbox_repo = OutboxRepository(db_session)
    lg_events = [
        event
        for event in await outbox_repo.fetch_pending(limit=100)
        if event.event_type == "LearningGraphUpdated"
    ]
    assert len(lg_events) >= 1
    assessment_events = [
        event for event in lg_events if event.correlation_id == "s47-e2e-assessment"
    ]
    assert len(assessment_events) == 1
    assert "confidence" in assessment_events[0].payload["changed_scores"]
