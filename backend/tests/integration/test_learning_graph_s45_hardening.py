from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from test_learning_graph_event_handlers import _provision_graph_for_student

from prepos.application.learning_graph.services import LearningGraphService
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.scoring.confidence_v1 import CONFIDENCE_V1
from prepos.domain.scoring.importance_copy_v1 import IMPORTANCE_COPY_V1
from prepos.domain.scoring.mastery_nonmcq_v1 import MASTERY_NONMCQ_V1
from prepos.domain.scoring.mastery_v1 import MASTERY_V1
from prepos.domain.scoring.retention_v1 import RETENTION_V1
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.models.learning_graph import LearningGraphEventModel, StudentConceptProgressModel
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork
from prepos.infrastructure.db.repositories.learning_graph_repository import SqlAlchemyLearningGraphRepository


@pytest.mark.asyncio
async def test_provisioned_nodes_have_null_retention_and_unrated_state(
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

    assert row.node_state == NodeStatus.UNRATED
    assert row.retention_score is None
    assert row.confidence_score is None
    assert row.mastery_version == MASTERY_V1
    assert row.mastery_nonmcq_version == MASTERY_NONMCQ_V1
    assert row.retention_version == RETENTION_V1
    assert row.confidence_version == CONFIDENCE_V1
    assert row.importance_version == IMPORTANCE_COPY_V1


@pytest.mark.asyncio
async def test_mutation_persists_scoring_versions_and_event_replay_metadata(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)

    service = LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(db_session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(db_session),
        outbox=OutboxPublisher(db_session),
        cache=NoOpLearningGraphCache(),
    )
    await service.handle_assessment_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        mcq_correct=True,
        self_confidence=None,
        correlation_id="s45-metadata-corr",
        causation_id="s45-metadata-cause",
    )
    await db_session.commit()

    node = (
        await db_session.execute(
            select(StudentConceptProgressModel).where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id == concept_id,
            )
        )
    ).scalar_one()
    assert node.mastery_version == MASTERY_V1
    assert node.confidence_version == CONFIDENCE_V1
    assert node.node_state == NodeStatus.RATED
    assert node.retention_score is None

    event = (
        await db_session.execute(
            select(LearningGraphEventModel)
            .where(
                LearningGraphEventModel.student_id == UUID(student_id),
                LearningGraphEventModel.concept_id == concept_id,
                LearningGraphEventModel.event_type == "AssessmentCompleted",
            )
            .order_by(LearningGraphEventModel.recorded_at.desc())
            .limit(1)
        )
    ).scalar_one()

    assert event.event_version == 1
    assert event.occurred_at is not None
    assert event.recorded_at is not None
    assert event.scoring_versions == {
        "mastery": MASTERY_V1,
        "mastery_nonmcq": MASTERY_NONMCQ_V1,
        "retention": RETENTION_V1,
        "confidence": CONFIDENCE_V1,
        "importance": IMPORTANCE_COPY_V1,
    }
    assert event.causation_id == "s45-metadata-cause"
    assert "changed_scores" in event.event_payload


def test_migration_005_lifecycle_value_map() -> None:
    lifecycle_migration = {
        "unstarted": NodeStatus.UNRATED,
        "active": NodeStatus.RATED,
    }
    assert lifecycle_migration["unstarted"] == "unrated"
    assert lifecycle_migration["active"] == "rated"


@pytest.mark.asyncio
async def test_api_exposes_nullable_retention_and_node_state(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from test_learning_graph_event_handlers import _login_student

    tenant_id, student_id, _ = await _provision_graph_for_student(client, db_session)
    student_token = await _login_student(client, slug="lg-event-handlers", email="student-lg-events@example.com")
    headers = {"Authorization": f"Bearer {student_token}"}

    overview = (await client.get("/api/v1/learning-graph", headers=headers, params={"limit": 1})).json()
    node = overview["nodes"][0]
    assert node["node_state"] == NodeStatus.UNRATED
    assert node["retention_score"] is None
    assert "status" not in node

    await LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(db_session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(db_session),
        outbox=OutboxPublisher(db_session),
        cache=NoOpLearningGraphCache(),
    ).handle_assessment_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=node["concept_id"],
        mcq_correct=True,
        self_confidence=None,
        correlation_id="s45-api-corr",
        causation_id=str(uuid4()),
    )
    await db_session.commit()

    detail = (
        await client.get(
            f"/api/v1/learning-graph/nodes/{node['concept_id']}",
            headers=headers,
        )
    ).json()
    assert detail["node_state"] == NodeStatus.RATED
    assert detail["retention_score"] is None
