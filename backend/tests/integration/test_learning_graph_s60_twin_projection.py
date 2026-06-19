from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from test_learning_graph_event_handlers import _provision_graph_for_student

from prepos.application.learning_graph.services import LearningGraphService
from prepos.events.dispatcher import dispatcher
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.models.student import PreparationTwinModel
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


async def _dispatch_latest_lg_event(db_session: AsyncSession, correlation_id: str) -> None:
    lg_event = next(
        event
        for event in await OutboxRepository(db_session).fetch_pending(limit=200)
        if event.event_type == "LearningGraphUpdated" and event.correlation_id == correlation_id
    )
    await dispatcher.dispatch(lg_event)
    await db_session.commit()


async def _dispatch_pending_twin_projection_events(db_session: AsyncSession) -> None:
    pending = await OutboxRepository(db_session).fetch_pending(limit=200)
    for event in pending:
        if event.event_type in {"RevisionQueueUpdated", "TwinRecommendationsUpdated"}:
            await dispatcher.dispatch(event)
    await db_session.commit()


@pytest.mark.asyncio
async def test_twin_projection_persists_profile_and_payload(
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
        correlation_id="s60-twin-projection",
        causation_id="s60-twin-projection",
    )
    await db_session.commit()
    await _dispatch_latest_lg_event(db_session, "s60-twin-projection")
    await _dispatch_pending_twin_projection_events(db_session)

    twin = (
        await db_session.execute(
            select(PreparationTwinModel).where(
                PreparationTwinModel.student_id == UUID(student_id),
            )
        )
    ).scalar_one()

    assert twin.profile_version == "TWIN_PROFILE_V1"
    assert twin.generated_at is not None
    assert twin.twin_payload
    assert twin.twin_payload["readiness"]["version"] == "readiness_v1_1"
    assert "overall_score" in twin.twin_payload["readiness"]
    assert "coverage_subscore" in twin.twin_payload["readiness"]
    assert "readiness" in twin.twin_payload
    assert "revision_queue" in twin.twin_payload
    assert "recommendations" in twin.twin_payload
    assert "drivers" in twin.twin_payload


@pytest.mark.asyncio
async def test_twin_updated_event_emitted(
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
        correlation_id="s60-twin-event",
        causation_id="s60-twin-event",
    )
    await db_session.commit()
    await _dispatch_latest_lg_event(db_session, "s60-twin-event")

    outbox = await OutboxRepository(db_session).fetch_pending(limit=200)
    twin_updated = [event for event in outbox if event.event_type == "TwinUpdated"]
    assert len(twin_updated) >= 1
    payload = twin_updated[-1].payload
    assert payload["profile_version"] == "TWIN_PROFILE_V1"
    assert payload["student_id"] == student_id


@pytest.mark.asyncio
async def test_twin_api_contract(
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
        correlation_id="s60-twin-api",
        causation_id="s60-twin-api",
    )
    await db_session.commit()
    await _dispatch_latest_lg_event(db_session, "s60-twin-api")

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "lg-event-handlers",
            "email": "student-lg-events@example.com",
            "password": "SecurePass123!",
        },
    )
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    twin_response = await client.get(
        "/api/v1/twin",
        headers=headers,
        params={"student_id": student_id},
    )
    assert twin_response.status_code == 200
    twin_payload = twin_response.json()
    assert twin_payload["profile_version"] == "TWIN_PROFILE_V1"
    assert twin_payload["twin_payload"]["readiness"]["version"] == "readiness_v1_1"
    assert "twin_payload" in twin_payload
    assert twin_payload["generated_at"] is not None


@pytest.mark.asyncio
async def test_twin_dashboard_api_contract(
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
        correlation_id="s60-dashboard-api",
        causation_id="s60-dashboard-api",
    )
    await db_session.commit()
    await _dispatch_latest_lg_event(db_session, "s60-dashboard-api")

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
        "/api/v1/twin/dashboard",
        headers=headers,
        params={"student_id": student_id},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "readiness_score" in payload
    assert "due_revision_count" in payload
    assert "high_risk_concept_count" in payload
    assert "recommendation_count" in payload
    assert "largest_positive_driver" in payload
    assert "largest_negative_driver" in payload
    assert "top_positive_drivers" in payload
    assert "top_negative_drivers" in payload
    assert "twin_payload" not in payload
