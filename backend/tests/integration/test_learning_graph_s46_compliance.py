from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from test_learning_graph_event_handlers import (
    _login_student,
    _provision_graph_for_student,
)

from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.scoring.weakness_v1 import WeaknessInputs, compute_weakness_v1
from prepos.infrastructure.db.models.learning_graph import StudentConceptProgressModel


@pytest.mark.asyncio
async def test_provisioned_node_confidence_is_null(
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


@pytest.mark.asyncio
async def test_weakness_api_excludes_unrated_nodes(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _provision_graph_for_student(client, db_session)
    student_token = await _login_student(client, slug="lg-event-handlers", email="student-lg-events@example.com")
    headers = {"Authorization": f"Bearer {student_token}"}

    response = await client.get("/api/v1/learning-graph/weaknesses", headers=headers)
    assert response.status_code == 200
    assert response.json()["weaknesses"] == []


@pytest.mark.asyncio
async def test_api_exposes_null_confidence_on_provisioned_node(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _provision_graph_for_student(client, db_session)
    student_token = await _login_student(client, slug="lg-event-handlers", email="student-lg-events@example.com")
    headers = {"Authorization": f"Bearer {student_token}"}

    overview = (await client.get("/api/v1/learning-graph", headers=headers, params={"limit": 1})).json()
    node = overview["nodes"][0]
    assert node["confidence_score"] is None
    assert node["retention_score"] is None
    assert node["node_state"] == NodeStatus.UNRATED


def test_weakness_engine_null_retention_and_confidence_behaviour() -> None:
    null_retention = compute_weakness_v1(
        WeaknessInputs(mastery=Decimal("50"), retention=None, error_rate=Decimal("0"))
    )
    null_confidence = compute_weakness_v1(
        WeaknessInputs(mastery=Decimal("50"), retention=Decimal("50"), confidence=None)
    )

    assert null_retention.value == Decimal("39.29")
    assert null_confidence.value == Decimal("42.50")


@pytest.mark.asyncio
async def test_migration_006_clears_unrated_confidence_to_null(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, student_id, concept_id = await _provision_graph_for_student(client, db_session)

    await db_session.execute(
        text(
            """
            UPDATE student_concept_progress
            SET confidence_score = 0
            WHERE student_id = :student_id AND concept_id = :concept_id
            """
        ),
        {"student_id": UUID(student_id), "concept_id": concept_id},
    )
    await db_session.commit()

    await db_session.execute(
        text(
            """
            UPDATE student_concept_progress
            SET confidence_score = NULL
            WHERE node_state = 'unrated' AND confidence_score = 0
            """
        )
    )
    await db_session.commit()

    row = (
        await db_session.execute(
            select(StudentConceptProgressModel).where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id == concept_id,
            )
        )
    ).scalar_one()

    assert row.confidence_score is None
