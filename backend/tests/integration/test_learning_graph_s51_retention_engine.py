from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from test_learning_graph_event_handlers import _provision_graph_for_student

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.services import LearningGraphService
from prepos.domain.scoring.retention_v1 import (
    RetentionInputs,
    apply_revision_retention_update,
    compute_next_review_at,
    compute_retention_score_from_state,
    compute_retention_v1,
    initialize_stability_from_mastery,
    recall_grade_to_int,
)
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
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


def test_initialize_stability_from_mastery_tiers() -> None:
    assert initialize_stability_from_mastery(Decimal("85")) == Decimal("30")
    assert initialize_stability_from_mastery(Decimal("80")) == Decimal("30")
    assert initialize_stability_from_mastery(Decimal("65")) == Decimal("14")
    assert initialize_stability_from_mastery(Decimal("40")) == Decimal("7")
    assert initialize_stability_from_mastery(Decimal("20")) == Decimal("3")


def test_retention_decays_over_time() -> None:
    review_at = datetime(2026, 1, 1, tzinfo=UTC)
    stability = Decimal("30")
    later = review_at + timedelta(days=30)

    immediate = compute_retention_score_from_state(
        stability_s=stability,
        last_review_at=review_at,
        current_time=review_at,
    )
    decayed = compute_retention_score_from_state(
        stability_s=stability,
        last_review_at=review_at,
        current_time=later,
    )

    assert immediate == Decimal("100.00")
    assert decayed == Decimal("36.79")


def test_next_review_at_from_stability() -> None:
    review_at = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    next_review = compute_next_review_at(last_review_at=review_at, stability_s=Decimal("14"))
    assert next_review == review_at + timedelta(days=14)


def test_unrated_node_returns_unrated_retention() -> None:
    result = compute_retention_v1(
        RetentionInputs(
            mastery_score=Decimal("50"),
            retention_stability_s=None,
            retention_last_review_at=None,
            retention_last_grade=None,
            current_time=datetime.now(UTC),
            node_state="unrated",
        )
    )
    assert result.unrated is True
    assert result.value is None
    assert result.stability_s is None


@pytest.mark.asyncio
async def test_assessment_does_not_update_retention_stability(
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
        correlation_id="s51-assessment",
        causation_id="s51-assessment",
    )
    await db_session.commit()

    assert updated.retention_score is None
    assert updated.retention_stability_s is None
    assert updated.retention_last_review_at is None


@pytest.mark.asyncio
async def test_revision_updates_retention_stability_and_score(
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
        correlation_id="s51-revision",
        causation_id="s51-revision",
    )
    await db_session.commit()

    assert updated.retention_score == Decimal("100")
    assert updated.retention_stability_s == Decimal("4.5000")
    assert updated.retention_last_review_at is not None
    assert updated.retention_last_grade == recall_grade_to_int("good")


@pytest.mark.asyncio
async def test_study_session_does_not_update_retention_stability(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    revised = await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s51-revise-before-study",
        causation_id="s51-revise-before-study",
    )
    await db_session.commit()

    studied = await service.handle_study_session_logged(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        engaged_minutes=20,
        correlation_id="s51-study",
        causation_id="s51-study",
    )
    await db_session.commit()

    assert studied.retention_stability_s == revised.retention_stability_s
    assert studied.retention_last_review_at == revised.retention_last_review_at
    assert studied.retention_last_grade == revised.retention_last_grade
    assert studied.retention_last_event_at is not None
    assert studied.retention_last_event_at >= revised.retention_last_event_at


@pytest.mark.asyncio
async def test_retention_materialization_on_read(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)
    read_service = _build_read_service(db_session)

    await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s51-read-materialize",
        causation_id="s51-read-materialize",
    )
    await db_session.commit()

    node_dto = await read_service.get_node(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
    )

    assert node_dto.retention_score == Decimal("100.00")
    assert node_dto.next_review_at is not None
    assert node_dto.retention_stability_s is not None


@pytest.mark.asyncio
async def test_learning_graph_updated_includes_retention_on_revision(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="easy",
        correlation_id="s51-lg-updated",
        causation_id="s51-lg-updated",
    )
    await db_session.commit()

    events = [
        event
        for event in await OutboxRepository(db_session).fetch_pending(limit=100)
        if event.event_type == "LearningGraphUpdated" and event.correlation_id == "s51-lg-updated"
    ]
    assert len(events) == 1
    assert "retention" in events[0].payload["changed_scores"]


def test_apply_revision_retention_initializes_from_mastery() -> None:
    now = datetime(2026, 6, 1, tzinfo=UTC)
    stability, score, review_at, event_at, grade = apply_revision_retention_update(
        mastery_score=Decimal("85"),
        prior_stability_s=None,
        recall_grade="good",
        current_time=now,
    )

    assert score == Decimal("100")
    assert stability == Decimal("45.0000")
    assert review_at == now
    assert event_at == now
    assert grade == recall_grade_to_int("good")
