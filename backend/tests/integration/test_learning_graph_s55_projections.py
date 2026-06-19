from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from test_learning_graph_event_handlers import _provision_graph_for_student

from prepos.application.learning_graph.services import LearningGraphService
from prepos.application.revision_queue.projector import RevisionQueueProjector
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.revision_queue.value_objects import RevisionQueueStatus
from prepos.events.dispatcher import dispatcher
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.models.learning_graph import StudentConceptProgressModel
from prepos.infrastructure.db.models.revision_queue import StudentRevisionQueueModel
from prepos.infrastructure.db.models.student import PreparationTwinModel
from prepos.infrastructure.db.repositories.event_repository import OutboxRepository
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork
from prepos.infrastructure.db.repositories.learning_graph_repository import SqlAlchemyLearningGraphRepository
from prepos.infrastructure.db.repositories.revision_queue_repository import SqlAlchemyRevisionQueueRepository


def _build_service(db_session: AsyncSession) -> LearningGraphService:
    return LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(db_session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(db_session),
        outbox=OutboxPublisher(db_session),
        cache=NoOpLearningGraphCache(),
    )


async def _dispatch_latest_lg_event(db_session: AsyncSession, correlation_id: str) -> None:
    lg_event = next(
        event
        for event in await OutboxRepository(db_session).fetch_pending(limit=200)
        if event.event_type == "LearningGraphUpdated" and event.correlation_id == correlation_id
    )
    await dispatcher.dispatch(lg_event)
    await db_session.commit()


@pytest.mark.asyncio
async def test_queue_row_created_on_revision(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s55-queue-create",
        causation_id="s55-queue-create",
    )
    await db_session.commit()
    await _dispatch_latest_lg_event(db_session, "s55-queue-create")

    row = (
        await db_session.execute(
            select(StudentRevisionQueueModel).where(
                StudentRevisionQueueModel.student_id == UUID(student_id),
                StudentRevisionQueueModel.concept_id == concept_id,
            )
        )
    ).scalar_one()

    assert row.status == RevisionQueueStatus.SCHEDULED
    assert row.priority_score > Decimal("0")
    assert row.weakness_score is not None


@pytest.mark.asyncio
async def test_queue_row_deleted_for_unrated_node(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    node = await SqlAlchemyLearningGraphRepository(db_session).get_node(
        UUID(tenant_id),
        UUID(student_id),
        concept_id,
    )
    assert node is not None
    assert node.node_state == NodeStatus.UNRATED

    projector = RevisionQueueProjector(
        graph_repo=SqlAlchemyLearningGraphRepository(db_session),
        queue_repo=SqlAlchemyRevisionQueueRepository(db_session),
        outbox=OutboxPublisher(db_session),
    )
    await projector.project_concept(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        exam_id=node.exam_id,
        concept_id=concept_id,
        correlation_id="s55-delete-unrated",
        causation_id=None,
    )
    await db_session.commit()

    count = (
        await db_session.execute(
            select(func.count())
            .select_from(StudentRevisionQueueModel)
            .where(StudentRevisionQueueModel.student_id == UUID(student_id))
        )
    ).scalar_one()
    assert count == 0


@pytest.mark.asyncio
async def test_due_status_when_overdue(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s55-due-status",
        causation_id="s55-due-status",
    )
    await db_session.commit()

    await db_session.execute(
        update(StudentConceptProgressModel)
        .where(
            StudentConceptProgressModel.student_id == UUID(student_id),
            StudentConceptProgressModel.concept_id == concept_id,
        )
        .values(
            retention_last_review_at=datetime.now(UTC) - timedelta(days=40),
            retention_stability_s=Decimal("10"),
        )
    )
    await db_session.commit()

    node = await SqlAlchemyLearningGraphRepository(db_session).get_node(
        UUID(tenant_id),
        UUID(student_id),
        concept_id,
    )
    assert node is not None
    projector = RevisionQueueProjector(
        graph_repo=SqlAlchemyLearningGraphRepository(db_session),
        queue_repo=SqlAlchemyRevisionQueueRepository(db_session),
        outbox=OutboxPublisher(db_session),
    )
    await projector.project_concept(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        exam_id=node.exam_id,
        concept_id=concept_id,
        correlation_id="s55-due-status",
        causation_id=None,
    )
    await db_session.commit()

    row = (
        await db_session.execute(
            select(StudentRevisionQueueModel).where(
                StudentRevisionQueueModel.student_id == UUID(student_id),
                StudentRevisionQueueModel.concept_id == concept_id,
            )
        )
    ).scalar_one()
    assert row.status == RevisionQueueStatus.DUE


@pytest.mark.asyncio
async def test_queue_ordering_by_priority(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_a = await _provision_graph_for_student(client, db_session)
    concept_b = (
        await db_session.execute(
            select(StudentConceptProgressModel.concept_id)
            .where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id != concept_a,
            )
            .limit(1)
        )
    ).scalar_one()
    service = _build_service(db_session)

    for concept_id, corr in [(concept_a, "s55-order-a"), (concept_b, "s55-order-b")]:
        await service.handle_revision_completed(
            tenant_id=UUID(tenant_id),
            student_id=UUID(student_id),
            concept_id=concept_id,
            recall_grade="good",
            correlation_id=corr,
            causation_id=corr,
        )
    await db_session.commit()

    await db_session.execute(
        update(StudentConceptProgressModel)
        .where(
            StudentConceptProgressModel.student_id == UUID(student_id),
            StudentConceptProgressModel.concept_id == concept_b,
        )
        .values(importance_score=Decimal("95"))
    )
    await db_session.commit()

    for corr in ["s55-order-a", "s55-order-b"]:
        await _dispatch_latest_lg_event(db_session, corr)

    repo = SqlAlchemyRevisionQueueRepository(db_session)
    queue = await repo.list_queue(UUID(tenant_id), UUID(student_id), limit=10)
    assert len(queue) >= 2
    assert queue[0].priority_score >= queue[1].priority_score


@pytest.mark.asyncio
async def test_twin_snapshot_projection(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    await service.handle_assessment_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        mcq_correct=True,
        self_confidence=None,
        correlation_id="s55-snapshot",
        causation_id="s55-snapshot",
    )
    await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s55-snapshot-revision",
        causation_id="s55-snapshot-revision",
    )
    await db_session.commit()

    for corr in ["s55-snapshot", "s55-snapshot-revision"]:
        await _dispatch_latest_lg_event(db_session, corr)

    twin = (
        await db_session.execute(
            select(PreparationTwinModel).where(
                PreparationTwinModel.student_id == UUID(student_id),
            )
        )
    ).scalar_one()

    assert twin.generated_at is not None
    assert twin.readiness_score is not None
    assert twin.largest_positive_driver is not None
    assert twin.largest_negative_driver is not None


@pytest.mark.asyncio
async def test_revision_queue_api(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s55-queue-api",
        causation_id="s55-queue-api",
    )
    await db_session.commit()
    await _dispatch_latest_lg_event(db_session, "s55-queue-api")

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
        "/api/v1/learning-graph/revisions/queue",
        headers=headers,
        params={"student_id": student_id},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1
    assert payload[0]["concept_id"] == concept_id
    assert "priority_score" in payload[0]


@pytest.mark.asyncio
async def test_twin_snapshot_api(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s55-snapshot-api",
        causation_id="s55-snapshot-api",
    )
    await db_session.commit()
    await _dispatch_latest_lg_event(db_session, "s55-snapshot-api")

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
        "/api/v1/twin/snapshot",
        headers=headers,
        params={"student_id": student_id},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "readiness_score" in payload
    assert "due_revision_count" in payload
    assert "largest_positive_driver" in payload


@pytest.mark.asyncio
async def test_duplicate_learning_graph_updated_idempotent(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)

    await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s55-idempotent",
        causation_id="s55-idempotent",
    )
    await db_session.commit()

    lg_event = next(
        event
        for event in await OutboxRepository(db_session).fetch_pending(limit=200)
        if event.event_type == "LearningGraphUpdated" and event.correlation_id == "s55-idempotent"
    )

    await dispatcher.dispatch(lg_event)
    await db_session.commit()
    count_after_first = (
        await db_session.execute(
            select(func.count())
            .select_from(StudentRevisionQueueModel)
            .where(
                StudentRevisionQueueModel.student_id == UUID(student_id),
                StudentRevisionQueueModel.concept_id == concept_id,
            )
        )
    ).scalar_one()

    await dispatcher.dispatch(lg_event)
    await db_session.commit()
    count_after_second = (
        await db_session.execute(
            select(func.count())
            .select_from(StudentRevisionQueueModel)
            .where(
                StudentRevisionQueueModel.student_id == UUID(student_id),
                StudentRevisionQueueModel.concept_id == concept_id,
            )
        )
    ).scalar_one()

    assert count_after_first == 1
    assert count_after_second == 1
