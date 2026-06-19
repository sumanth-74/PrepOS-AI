from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from test_learning_graph_event_handlers import _provision_graph_for_student

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.services import LearningGraphService
from prepos.application.twin.services import TwinRecommendationService
from prepos.events.dispatcher import dispatcher
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.models.twin import PreparationTwinRecommendationModel
from prepos.infrastructure.db.repositories.event_repository import OutboxRepository
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork
from prepos.infrastructure.db.repositories.learning_graph_repository import (
    SqlAlchemyLearningGraphReadRepository,
    SqlAlchemyLearningGraphRepository,
)
from prepos.infrastructure.db.repositories.twin_repository import SqlAlchemyTwinRecommendationRepository


def _build_service(db_session: AsyncSession) -> LearningGraphService:
    return LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(db_session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(db_session),
        outbox=OutboxPublisher(db_session),
        cache=NoOpLearningGraphCache(),
    )


def _build_twin_service(db_session: AsyncSession) -> TwinRecommendationService:
    return TwinRecommendationService(
        learning_graph_read_service=LearningGraphReadService(
            read_repo=SqlAlchemyLearningGraphReadRepository(db_session),
            write_repo=SqlAlchemyLearningGraphRepository(db_session),
            cache=NoOpLearningGraphCache(),
        ),
        recommendation_repo=SqlAlchemyTwinRecommendationRepository(db_session),
        outbox=OutboxPublisher(db_session),
    )


@pytest.mark.asyncio
async def test_twin_recommendations_api(
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
        correlation_id="s54-api-revision",
        causation_id="s54-api-revision",
    )
    await db_session.commit()

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
        "/api/v1/twin/recommendations",
        headers=headers,
        params={"student_id": student_id, "limit": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1
    item = payload[0]
    assert item["concept_id"] == concept_id
    assert item["recommendation_type"] in {
        "WEAKNESS_RECOVERY",
        "REVISION_DUE",
        "HIGH_IMPORTANCE_GAP",
        "READINESS_BOOST",
    }
    assert "recommendation_score" in item
    assert "explanation" in item


@pytest.mark.asyncio
async def test_learning_graph_updated_recomputes_recommendations(
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
        correlation_id="s54-lg-updated",
        causation_id="s54-lg-updated",
    )
    await db_session.commit()

    lg_events = [
        event
        for event in await OutboxRepository(db_session).fetch_pending(limit=100)
        if event.event_type == "LearningGraphUpdated" and event.correlation_id == "s54-lg-updated"
    ]
    assert len(lg_events) == 1

    await dispatcher.dispatch(lg_events[0])
    await db_session.commit()

    persisted_count = (
        await db_session.execute(
            select(func.count())
            .select_from(PreparationTwinRecommendationModel)
            .where(PreparationTwinRecommendationModel.student_id == UUID(student_id))
        )
    ).scalar_one()
    assert persisted_count >= 1

    twin_events = [
        event
        for event in await OutboxRepository(db_session).fetch_pending(limit=100)
        if event.event_type == "TwinRecommendationsUpdated"
    ]
    assert len(twin_events) >= 1
    assert twin_events[-1].payload["exam_id"] == updated.exam_id
    assert concept_id in twin_events[-1].payload["concept_ids"]
