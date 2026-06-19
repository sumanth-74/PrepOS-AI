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
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
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
async def test_readiness_snapshot_integration(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)
    read_service = _build_read_service(db_session)

    await service.handle_assessment_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        mcq_correct=True,
        self_confidence=None,
        correlation_id="s53-readiness-assessment",
        causation_id="s53-readiness-assessment",
    )
    await service.handle_revision_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        recall_grade="good",
        correlation_id="s53-readiness-revision",
        causation_id="s53-readiness-revision",
    )
    await db_session.commit()

    readiness = await read_service.get_readiness(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
    )

    assert readiness.version == "readiness_v1_1"
    assert readiness.unrated is False
    assert readiness.rated_node_count == 1
    assert readiness.total_node_count > 0
    assert readiness.knowledge_subscore is not None
    assert readiness.retention_subscore == Decimal("100.00")
    assert readiness.confidence_subscore is not None
    assert readiness.coverage_subscore is not None
    assert readiness.overall_score is not None
    assert readiness.readiness_score == readiness.overall_score
    assert readiness.overall_score > Decimal("0")


@pytest.mark.asyncio
async def test_readiness_zero_coverage_without_rated_nodes(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, _ = await _provision_graph_for_student(client, db_session)
    read_service = _build_read_service(db_session)

    readiness = await read_service.get_readiness(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
    )

    assert readiness.unrated is False
    assert readiness.rated_node_count == 0
    assert readiness.total_node_count > 0
    assert readiness.coverage_subscore == Decimal("0.00")
    assert readiness.overall_score == Decimal("0.00")


@pytest.mark.asyncio
async def test_readiness_api(
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
        correlation_id="s53-readiness-api",
        causation_id="s53-readiness-api",
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
        "/api/v1/learning-graph/readiness",
        headers=headers,
        params={"student_id": student_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "readiness_v1_1"
    assert payload["unrated"] is False
    assert payload["rated_node_count"] == 1
    assert payload["total_node_count"] > 0
    assert payload["overall_score"] is not None
    assert payload["readiness_score"] == payload["overall_score"]
    assert payload["knowledge_subscore"] is not None
    assert payload["retention_subscore"] is not None
    assert "confidence_subscore" in payload
    assert "coverage_subscore" in payload


@pytest.mark.asyncio
async def test_readiness_drivers_from_service_snapshot(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)
    service = _build_service(db_session)
    read_service = _build_read_service(db_session)

    await service.handle_assessment_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        mcq_correct=True,
        self_confidence=None,
        correlation_id="s53-drivers-assessment",
        causation_id="s53-drivers-assessment",
    )
    await db_session.commit()

    now = datetime.now(UTC)
    snapshot = await read_service.get_readiness_snapshot(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        current_time=now + timedelta(days=60),
    )

    from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
    from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot

    result, drivers = compute_readiness_from_snapshot(
        LearningGraphReadinessSnapshot(
            average_mastery=snapshot.average_mastery,
            average_retention=snapshot.average_retention,
            average_confidence=snapshot.average_confidence,
            rated_node_count=snapshot.rated_node_count,
            total_node_count=snapshot.total_node_count,
        )
    )

    assert result.unrated is False
    assert drivers is not None
    assert drivers.largest_positive_driver in {"knowledge", "retention", "confidence", "coverage"}
    assert drivers.largest_negative_driver in {"knowledge", "retention", "confidence", "coverage"}
    assert len(drivers.top_positive_drivers) >= 1
    assert len(drivers.top_negative_drivers) >= 1
