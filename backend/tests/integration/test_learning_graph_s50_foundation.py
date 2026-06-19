from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from test_learning_graph_event_handlers import _provision_graph_for_student

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.services import LearningGraphService
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.models.learning_graph import ScoreAuditLogModel, StudentConceptProgressModel
from prepos.infrastructure.db.repositories.event_repository import OutboxRepository
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork
from prepos.infrastructure.db.repositories.learning_graph_repository import (
    SqlAlchemyLearningGraphReadRepository,
    SqlAlchemyLearningGraphRepository,
)


def _build_service(db_session: AsyncSession) -> LearningGraphService:
    return LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(db_session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(db_session),
        outbox=OutboxPublisher(db_session),
        cache=NoOpLearningGraphCache(),
    )


def _build_read_service(db_session: AsyncSession) -> LearningGraphReadService:
    return LearningGraphReadService(
        read_repo=SqlAlchemyLearningGraphReadRepository(db_session),
        write_repo=SqlAlchemyLearningGraphRepository(db_session),
        cache=NoOpLearningGraphCache(),
    )


@pytest.mark.asyncio
async def test_provisioned_nodes_have_null_retention_state_columns(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, student_id, concept_id = await _provision_graph_for_student(client, db_session)

    row = (
        await db_session.execute(
            select(StudentConceptProgressModel).where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id == concept_id,
            )
        )
    ).scalar_one()

    assert row.retention_stability_s is None
    assert row.retention_last_event_at is None
    assert row.retention_last_review_at is None
    assert row.retention_last_grade is None


@pytest.mark.asyncio
async def test_score_audit_value_to_null_transition(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    rated = await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s50-audit-null-revision",
        causation_id="s50-audit-null-revision",
    )
    assert rated.retention_score is not None

    cleared = replace(rated, retention_score=None)
    await service._persist_mutation(
        previous=rated,
        updated=cleared,
        reason="TestRetentionClear",
        correlation_id="s50-audit-null-clear",
        causation_id="s50-audit-null-clear",
    )
    await db_session.commit()

    audit_row = (
        await db_session.execute(
            select(ScoreAuditLogModel)
            .where(
                ScoreAuditLogModel.student_id == UUID(student_id),
                ScoreAuditLogModel.concept_id == concept_id,
                ScoreAuditLogModel.score_type == "retention",
                ScoreAuditLogModel.new_value.is_(None),
            )
            .order_by(ScoreAuditLogModel.created_at.desc())
            .limit(1)
        )
    ).scalar_one()

    assert audit_row.previous_value is not None
    assert audit_row.new_value is None


@pytest.mark.asyncio
async def test_learning_graph_updated_emitted_when_scores_unchanged(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    node = (
        await db_session.execute(
            select(StudentConceptProgressModel).where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id == concept_id,
            )
        )
    ).scalar_one()
    importance = node.importance_score

    await service.handle_pyq_data_changed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        global_importance=importance,
        correlation_id="s50-pyq-first",
        causation_id="s50-pyq-first",
    )
    await db_session.commit()

    outbox_before = len(await OutboxRepository(db_session).fetch_pending(limit=200))

    await service.handle_pyq_data_changed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        global_importance=importance,
        correlation_id="s50-pyq-second",
        causation_id="s50-pyq-second",
    )
    await db_session.commit()

    outbox_after = await OutboxRepository(db_session).fetch_pending(limit=200)
    new_events = [
        event
        for event in outbox_after[outbox_before:]
        if event.event_type == "LearningGraphUpdated" and event.correlation_id == "s50-pyq-second"
    ]
    assert len(new_events) == 1
    assert new_events[0].payload["changed_scores"] == []
    assert new_events[0].payload["row_version"] >= 2


@pytest.mark.asyncio
async def test_summary_returns_null_weighted_averages_without_rated_nodes(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, _ = await _provision_graph_for_student(client, db_session)
    read_service = _build_read_service(db_session)

    summary = await read_service.get_summary(tenant_id=UUID(tenant_id), student_id=UUID(student_id))

    assert summary.total_nodes > 0
    assert summary.active_nodes == 0
    assert summary.average_mastery is None
    assert summary.average_retention is None
    assert summary.average_confidence is None


@pytest.mark.asyncio
async def test_summary_uses_importance_weighted_averages_for_rated_nodes(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)
    read_service = _build_read_service(db_session)

    updated = await service.handle_assessment_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        mcq_correct=True,
        self_confidence=None,
        correlation_id="s50-summary-corr",
        causation_id="s50-summary-cause",
    )
    revised = await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s50-summary-revision",
        causation_id="s50-summary-revision",
    )
    await db_session.commit()

    summary = await read_service.get_summary(tenant_id=UUID(tenant_id), student_id=UUID(student_id))

    assert summary.active_nodes == 1
    assert summary.average_mastery == revised.mastery_score
    assert summary.average_retention == revised.retention_score
    assert summary.average_confidence == updated.confidence_score


@pytest.mark.asyncio
async def test_summary_weighted_average_ignores_unrated_nodes(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)
    read_service = _build_read_service(db_session)

    revised = await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s50-weighted-revision",
        causation_id="s50-weighted-revision",
    )
    await db_session.commit()

    total_nodes = (
        await db_session.execute(
            select(func.count())
            .select_from(StudentConceptProgressModel)
            .where(StudentConceptProgressModel.student_id == UUID(student_id))
        )
    ).scalar_one()

    summary = await read_service.get_summary(tenant_id=UUID(tenant_id), student_id=UUID(student_id))

    assert total_nodes > 1
    assert summary.average_mastery == revised.mastery_score
    assert summary.average_mastery != Decimal("0.00")
