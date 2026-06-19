from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from test_learning_graph_event_handlers import _provision_graph_for_student

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.retention_materialization import (
    compute_due_for_revision,
    compute_graph_score_aggregates,
    due_revision_sort_key,
    materialize_node_retention,
)
from prepos.application.learning_graph.services import LearningGraphService
from prepos.domain.learning_graph.entities import ConceptProgressNode
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.scoring.retention_v1 import compute_retention_score_from_state
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.models.learning_graph import StudentConceptProgressModel
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


async def _second_concept_id(db_session: AsyncSession, student_id: str, *, skip: str) -> str:
    return (
        await db_session.execute(
            select(StudentConceptProgressModel.concept_id)
            .where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id != skip,
            )
            .order_by(StudentConceptProgressModel.concept_id.asc())
            .limit(1)
        )
    ).scalar_one()


async def _set_retention_state(
    db_session: AsyncSession,
    *,
    student_id: str,
    concept_id: str,
    review_at: datetime,
    stability_s: Decimal,
    importance_score: Decimal | None = None,
) -> None:
    values: dict[str, object] = {
        "node_state": NodeStatus.RATED,
        "retention_last_review_at": review_at,
        "retention_stability_s": stability_s,
        "retention_score": Decimal("100"),
        "retention_last_grade": 2,
    }
    if importance_score is not None:
        values["importance_score"] = importance_score
    await db_session.execute(
        update(StudentConceptProgressModel)
        .where(
            StudentConceptProgressModel.student_id == UUID(student_id),
            StudentConceptProgressModel.concept_id == concept_id,
        )
        .values(**values)
    )
    await db_session.commit()


def _node_from_row(row: StudentConceptProgressModel) -> ConceptProgressNode:
    return ConceptProgressNode(
        id=row.id,
        tenant_id=row.tenant_id,
        student_id=row.student_id,
        exam_id=row.exam_id,
        catalog_version=row.catalog_version,
        concept_id=row.concept_id,
        subject_id=row.subject_id,
        topic_id=row.topic_id,
        mastery_score=row.mastery_score,
        mastery_nonmcq_score=row.mastery_nonmcq_score,
        retention_score=row.retention_score,
        retention_stability_s=row.retention_stability_s,
        retention_last_event_at=row.retention_last_event_at,
        retention_last_review_at=row.retention_last_review_at,
        retention_last_grade=row.retention_last_grade,
        confidence_score=row.confidence_score,
        importance_score=row.importance_score,
        overconfidence_flag=row.overconfidence_flag,
        mcq_attempt_count=row.mcq_attempt_count,
        mcq_correct_count=row.mcq_correct_count,
        nonmcq_attempt_count=row.nonmcq_attempt_count,
        revision_count=row.revision_count,
        study_minutes=row.study_minutes,
        node_state=row.node_state,
        mastery_version=row.mastery_version,
        mastery_nonmcq_version=row.mastery_nonmcq_version,
        retention_version=row.retention_version,
        confidence_version=row.confidence_version,
        importance_version=row.importance_version,
        first_seen_at=row.first_seen_at,
        last_activity_at=row.last_activity_at,
        row_version=row.row_version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def test_compute_graph_score_aggregates_uses_materialized_retention() -> None:
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    review_recent = now
    review_old = now - timedelta(days=30)
    stability = Decimal("30")

    node_a = ConceptProgressNode(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        tenant_id=UUID("00000000-0000-0000-0000-000000000010"),
        student_id=UUID("00000000-0000-0000-0000-000000000020"),
        exam_id="upsc-cse",
        catalog_version="v1",
        concept_id="concept-a",
        subject_id="subject-a",
        topic_id="topic-a",
        mastery_score=Decimal("80"),
        mastery_nonmcq_score=Decimal("0"),
        retention_score=Decimal("100"),
        retention_stability_s=stability,
        retention_last_review_at=review_recent,
        retention_last_grade=2,
        confidence_score=Decimal("70"),
        importance_score=Decimal("50"),
        overconfidence_flag=False,
        mcq_attempt_count=1,
        mcq_correct_count=1,
        nonmcq_attempt_count=0,
        revision_count=1,
        study_minutes=0,
        node_state=NodeStatus.RATED,
        mastery_version="mastery_v1",
        mastery_nonmcq_version="mastery_nonmcq_v1",
        retention_version="retention_v1",
        confidence_version="confidence_v1",
        importance_version="importance_copy_v1",
        first_seen_at=review_recent,
        last_activity_at=review_recent,
        row_version=1,
    )
    node_b = ConceptProgressNode(
        id=UUID("00000000-0000-0000-0000-000000000002"),
        tenant_id=UUID("00000000-0000-0000-0000-000000000010"),
        student_id=UUID("00000000-0000-0000-0000-000000000020"),
        exam_id="upsc-cse",
        catalog_version="v1",
        concept_id="concept-b",
        subject_id="subject-b",
        topic_id="topic-b",
        mastery_score=Decimal("60"),
        mastery_nonmcq_score=Decimal("0"),
        retention_score=Decimal("100"),
        retention_stability_s=stability,
        retention_last_review_at=review_old,
        retention_last_grade=2,
        confidence_score=Decimal("60"),
        importance_score=Decimal("50"),
        overconfidence_flag=False,
        mcq_attempt_count=1,
        mcq_correct_count=1,
        nonmcq_attempt_count=0,
        revision_count=1,
        study_minutes=0,
        node_state=NodeStatus.RATED,
        mastery_version="mastery_v1",
        mastery_nonmcq_version="mastery_nonmcq_v1",
        retention_version="retention_v1",
        confidence_version="confidence_v1",
        importance_version="importance_copy_v1",
        first_seen_at=review_old,
        last_activity_at=review_old,
        row_version=1,
    )

    aggregates = compute_graph_score_aggregates((node_a, node_b), current_time=now)

    expected_retention = (
        Decimal("100") * Decimal("50") + Decimal("36.79") * Decimal("50")
    ) / Decimal("100")
    assert aggregates.average_retention == expected_retention.quantize(Decimal("0.01"))
    assert aggregates.average_retention != Decimal("100.00")
    assert aggregates.rated_node_count == 2


def test_compute_due_for_revision_rules() -> None:
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    review_at = now - timedelta(days=40)
    stability = Decimal("30")

    due_node = ConceptProgressNode(
        id=UUID("00000000-0000-0000-0000-000000000003"),
        tenant_id=UUID("00000000-0000-0000-0000-000000000010"),
        student_id=UUID("00000000-0000-0000-0000-000000000020"),
        exam_id="upsc-cse",
        catalog_version="v1",
        concept_id="due-concept",
        subject_id="subject-a",
        topic_id="topic-a",
        mastery_score=Decimal("80"),
        mastery_nonmcq_score=Decimal("0"),
        retention_score=Decimal("100"),
        retention_stability_s=stability,
        retention_last_review_at=review_at,
        retention_last_grade=2,
        confidence_score=Decimal("70"),
        importance_score=Decimal("50"),
        overconfidence_flag=False,
        mcq_attempt_count=1,
        mcq_correct_count=1,
        nonmcq_attempt_count=0,
        revision_count=1,
        study_minutes=0,
        node_state=NodeStatus.RATED,
        mastery_version="mastery_v1",
        mastery_nonmcq_version="mastery_nonmcq_v1",
        retention_version="retention_v1",
        confidence_version="confidence_v1",
        importance_version="importance_copy_v1",
        first_seen_at=review_at,
        last_activity_at=review_at,
        row_version=1,
    )
    not_due_node = replace(
        due_node,
        id=UUID("00000000-0000-0000-0000-000000000004"),
        concept_id="future-concept",
        retention_last_review_at=now - timedelta(days=1),
        retention_stability_s=Decimal("14"),
    )
    unrated_node = replace(
        due_node,
        id=UUID("00000000-0000-0000-0000-000000000005"),
        concept_id="unrated-concept",
        node_state=NodeStatus.UNRATED,
        retention_last_review_at=None,
        retention_stability_s=None,
    )
    assessment_only = replace(
        due_node,
        id=UUID("00000000-0000-0000-0000-000000000006"),
        concept_id="assessment-only",
        retention_last_review_at=None,
        retention_stability_s=None,
        retention_score=None,
    )

    assert compute_due_for_revision(due_node, current_time=now) is True
    assert compute_due_for_revision(not_due_node, current_time=now) is False
    assert compute_due_for_revision(unrated_node, current_time=now) is False
    assert compute_due_for_revision(assessment_only, current_time=now) is False


def test_due_revision_sort_key_ordering() -> None:
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    more_overdue = ConceptProgressNode(
        id=UUID("00000000-0000-0000-0000-000000000007"),
        tenant_id=UUID("00000000-0000-0000-0000-000000000010"),
        student_id=UUID("00000000-0000-0000-0000-000000000020"),
        exam_id="upsc-cse",
        catalog_version="v1",
        concept_id="more-overdue",
        subject_id="subject-a",
        topic_id="topic-a",
        mastery_score=Decimal("80"),
        mastery_nonmcq_score=Decimal("0"),
        retention_score=Decimal("100"),
        retention_stability_s=Decimal("10"),
        retention_last_review_at=now - timedelta(days=30),
        retention_last_grade=2,
        confidence_score=Decimal("70"),
        importance_score=Decimal("40"),
        overconfidence_flag=False,
        mcq_attempt_count=1,
        mcq_correct_count=1,
        nonmcq_attempt_count=0,
        revision_count=1,
        study_minutes=0,
        node_state=NodeStatus.RATED,
        mastery_version="mastery_v1",
        mastery_nonmcq_version="mastery_nonmcq_v1",
        retention_version="retention_v1",
        confidence_version="confidence_v1",
        importance_version="importance_copy_v1",
        first_seen_at=now,
        last_activity_at=now,
        row_version=1,
    )
    less_overdue_high_importance = replace(
        more_overdue,
        id=UUID("00000000-0000-0000-0000-000000000008"),
        concept_id="less-overdue",
        importance_score=Decimal("90"),
        retention_stability_s=Decimal("20"),
        retention_last_review_at=now - timedelta(days=25),
    )
    same_overdue_lower_importance = replace(
        more_overdue,
        id=UUID("00000000-0000-0000-0000-000000000009"),
        concept_id="same-overdue",
        importance_score=Decimal("30"),
        retention_stability_s=Decimal("10"),
        retention_last_review_at=now - timedelta(days=30),
    )

    ordered = sorted(
        [less_overdue_high_importance, same_overdue_lower_importance, more_overdue],
        key=lambda node: due_revision_sort_key(node, current_time=now),
    )

    assert [node.concept_id for node in ordered] == [
        "more-overdue",
        "same-overdue",
        "less-overdue",
    ]


@pytest.mark.asyncio
async def test_summary_uses_materialized_retention(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_a = await _provision_graph_for_student(client, db_session)
    concept_b = await _second_concept_id(db_session, student_id, skip=concept_a)
    read_service = _build_read_service(db_session)

    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    await _set_retention_state(
        db_session,
        student_id=student_id,
        concept_id=concept_a,
        review_at=now,
        stability_s=Decimal("30"),
        importance_score=Decimal("50"),
    )
    await _set_retention_state(
        db_session,
        student_id=student_id,
        concept_id=concept_b,
        review_at=now - timedelta(days=30),
        stability_s=Decimal("30"),
        importance_score=Decimal("50"),
    )

    summary = await read_service.get_summary(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
    )

    expected = (
        Decimal("100") * Decimal("50") + Decimal("36.79") * Decimal("50")
    ) / Decimal("100")
    assert summary.average_retention == expected.quantize(Decimal("0.01"))
    assert summary.average_retention != Decimal("100.00")


@pytest.mark.asyncio
async def test_summary_retention_decays_without_writes(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    read_service = _build_read_service(db_session)
    service = _build_service(db_session)

    await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s52-decay-summary",
        causation_id="s52-decay-summary",
    )
    await db_session.commit()

    summary_immediate = await read_service.get_summary(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
    )
    assert summary_immediate.average_retention == Decimal("100.00")

    row = (
        await db_session.execute(
            select(StudentConceptProgressModel).where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id == concept_id,
            )
        )
    ).scalar_one()
    review_at = row.retention_last_review_at
    assert review_at is not None
    stability = row.retention_stability_s
    assert stability is not None

    later = review_at + timedelta(days=30)
    expected_decayed = compute_retention_score_from_state(
        stability_s=stability,
        last_review_at=review_at,
        current_time=later,
    )
    node = _node_from_row(row)
    decayed = materialize_node_retention(node, current_time=later).value
    assert decayed == expected_decayed

    rated_nodes = await read_service._read_repo.list_rated_nodes(UUID(tenant_id), UUID(student_id))
    aggregates = compute_graph_score_aggregates(rated_nodes, current_time=later)
    assert aggregates.average_retention == expected_decayed


@pytest.mark.asyncio
async def test_readiness_snapshot_uses_materialized_retention(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_a = await _provision_graph_for_student(client, db_session)
    concept_b = await _second_concept_id(db_session, student_id, skip=concept_a)
    read_service = _build_read_service(db_session)

    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    await _set_retention_state(
        db_session,
        student_id=student_id,
        concept_id=concept_a,
        review_at=now,
        stability_s=Decimal("30"),
        importance_score=Decimal("50"),
    )
    await _set_retention_state(
        db_session,
        student_id=student_id,
        concept_id=concept_b,
        review_at=now - timedelta(days=30),
        stability_s=Decimal("30"),
        importance_score=Decimal("50"),
    )

    snapshot = await read_service.get_readiness_snapshot(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        current_time=now,
    )

    expected_retention = (
        Decimal("100") * Decimal("50") + Decimal("36.79") * Decimal("50")
    ) / Decimal("100")
    assert snapshot.average_retention == expected_retention.quantize(Decimal("0.01"))
    assert snapshot.rated_node_count == 2


@pytest.mark.asyncio
async def test_list_due_revisions_excludes_unrated_and_assessment_only(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_a = await _provision_graph_for_student(client, db_session)
    concept_b = await _second_concept_id(db_session, student_id, skip=concept_a)
    concept_c = (
        await db_session.execute(
            select(StudentConceptProgressModel.concept_id)
            .where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id.not_in([concept_a, concept_b]),
            )
            .order_by(StudentConceptProgressModel.concept_id.asc())
            .limit(1)
        )
    ).scalar_one()

    service = _build_service(db_session)
    read_service = _build_read_service(db_session)
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    await _set_retention_state(
        db_session,
        student_id=student_id,
        concept_id=concept_a,
        review_at=now - timedelta(days=40),
        stability_s=Decimal("30"),
    )
    await service.handle_assessment_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_b,
        mcq_correct=True,
        self_confidence=None,
        correlation_id="s52-assessment-only",
        causation_id="s52-assessment-only",
    )
    await db_session.commit()

    due_items = await read_service.list_due_revisions(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        current_time=now,
    )
    due_concept_ids = {item.concept_id for item in due_items}

    assert concept_a in due_concept_ids
    assert concept_b not in due_concept_ids
    assert concept_c not in due_concept_ids


@pytest.mark.asyncio
async def test_not_due_before_next_review_at(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    read_service = _build_read_service(db_session)
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    await _set_retention_state(
        db_session,
        student_id=student_id,
        concept_id=concept_id,
        review_at=now - timedelta(days=1),
        stability_s=Decimal("14"),
    )

    due_items = await read_service.list_due_revisions(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        current_time=now,
    )
    assert all(item.concept_id != concept_id for item in due_items)


@pytest.mark.asyncio
async def test_revision_queue_ordering(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_a = await _provision_graph_for_student(client, db_session)
    concept_b = await _second_concept_id(db_session, student_id, skip=concept_a)
    concept_c = (
        await db_session.execute(
            select(StudentConceptProgressModel.concept_id)
            .where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id.not_in([concept_a, concept_b]),
            )
            .order_by(StudentConceptProgressModel.concept_id.asc())
            .limit(1)
        )
    ).scalar_one()
    read_service = _build_read_service(db_session)
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    await _set_retention_state(
        db_session,
        student_id=student_id,
        concept_id=concept_a,
        review_at=now - timedelta(days=40),
        stability_s=Decimal("10"),
        importance_score=Decimal("40"),
    )
    await _set_retention_state(
        db_session,
        student_id=student_id,
        concept_id=concept_b,
        review_at=now - timedelta(days=40),
        stability_s=Decimal("10"),
        importance_score=Decimal("90"),
    )
    await _set_retention_state(
        db_session,
        student_id=student_id,
        concept_id=concept_c,
        review_at=now - timedelta(days=25),
        stability_s=Decimal("20"),
        importance_score=Decimal("95"),
    )

    due_items = await read_service.list_due_revisions(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        current_time=now,
    )
    assert [item.concept_id for item in due_items] == [concept_b, concept_a, concept_c]


@pytest.mark.asyncio
async def test_due_revisions_api(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    await _set_retention_state(
        db_session,
        student_id=student_id,
        concept_id=concept_id,
        review_at=now - timedelta(days=40),
        stability_s=Decimal("30"),
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "lg-event-handlers",
            "email": "student-lg-events@example.com",
            "password": "SecurePass123!",
        },
    )
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = await client.get(
        "/api/v1/learning-graph/revisions/due",
        headers=headers,
        params={"student_id": student_id, "limit": 10},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["concept_id"] == concept_id
    assert "next_review_at" in payload[0]
    assert "retention_score" in payload[0]
    assert "importance_score" in payload[0]
