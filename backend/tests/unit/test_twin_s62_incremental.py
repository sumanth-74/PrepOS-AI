from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from prepos.domain.learning_graph.entities import ConceptProgressNode
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.twin.recommendations_v1 import (
    MIN_RECOMMENDATION_SCORE,
    compute_recommendation_for_concept,
)
from prepos.domain.twin.twin_payload_v1 import merge_twin_payload_sections
from prepos.infrastructure.db.models.twin_rebuild_lock import TwinRebuildLockModel
from prepos.infrastructure.db.repositories.twin_rebuild_lock_repository import SqlAlchemyTwinRebuildLockRepository
from prepos.infrastructure.db.repositories.twin_snapshot_repository import SqlAlchemyTwinProjectionRepository


def _node(*, concept_id: str, mastery: Decimal = Decimal("40")) -> ConceptProgressNode:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    return ConceptProgressNode(
        id=uuid4(),
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        catalog_version="v1",
        concept_id=concept_id,
        subject_id="subject-a",
        topic_id="topic-a",
        mastery_score=mastery,
        mastery_nonmcq_score=Decimal("0"),
        retention_score=Decimal("100"),
        retention_stability_s=Decimal("30"),
        retention_last_review_at=now,
        retention_last_grade=2,
        confidence_score=Decimal("60"),
        importance_score=Decimal("85"),
        overconfidence_flag=False,
        mcq_attempt_count=1,
        mcq_correct_count=0,
        nonmcq_attempt_count=0,
        revision_count=1,
        study_minutes=0,
        node_state=NodeStatus.UNRATED,
        mastery_version="mastery_v1",
        mastery_nonmcq_version="mastery_nonmcq_v1",
        retention_version="retention_v1",
        confidence_version="confidence_v1",
        importance_version="importance_copy_v1",
        first_seen_at=now,
        last_activity_at=now,
        row_version=1,
    )


def test_compute_recommendation_for_concept_returns_none_when_unrated() -> None:
    assert (
        compute_recommendation_for_concept(
            _node(concept_id="concept-a"),
            weakness_score=Decimal("80"),
            is_due=False,
            readiness_result=None,
            readiness_drivers=None,
            current_time=datetime(2026, 6, 18, tzinfo=UTC),
        )
        is None
    )


def test_compute_recommendation_for_concept_deletes_below_threshold() -> None:
    rated = replace(
        _node(concept_id="concept-low"),
        node_state=NodeStatus.RATED,
        mastery_score=Decimal("95"),
        importance_score=Decimal("10"),
    )
    recommendation = compute_recommendation_for_concept(
        rated,
        weakness_score=Decimal("5"),
        is_due=False,
        readiness_result=None,
        readiness_drivers=None,
        current_time=datetime(2026, 6, 18, tzinfo=UTC),
    )
    assert recommendation is None or recommendation.recommendation_score >= MIN_RECOMMENDATION_SCORE


def test_merge_twin_payload_sections_preserves_unrelated_blocks() -> None:
    existing = {
        "profile_version": "TWIN_PROFILE_V1",
        "readiness": {"overall_score": 70.0},
        "revision_queue": {"due_revision_count": 2},
        "recommendations": {"recommendation_count": 1},
    }
    merged = merge_twin_payload_sections(
        existing,
        revision_queue={"due_revision_count": 5, "high_risk_concept_count": 1},
    )
    assert merged["readiness"] == {"overall_score": 70.0}
    assert merged["recommendations"] == {"recommendation_count": 1}
    assert merged["revision_queue"]["due_revision_count"] == 5


@pytest.mark.asyncio
async def test_rebuild_lock_expires_and_can_be_reacquired(db_session) -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    repo = SqlAlchemyTwinRebuildLockRepository(db_session)

    assert await repo.try_acquire_lock(
        tenant_id,
        student_id,
        exam_id,
        correlation_id="first",
        ttl_seconds=60,
    )
    assert not await repo.try_acquire_lock(
        tenant_id,
        student_id,
        exam_id,
        correlation_id="second",
        ttl_seconds=60,
    )

    lock = (
        await db_session.execute(
            select(TwinRebuildLockModel).where(
                TwinRebuildLockModel.tenant_id == tenant_id,
                TwinRebuildLockModel.student_id == student_id,
                TwinRebuildLockModel.exam_id == exam_id,
            )
        )
    ).scalar_one()
    lock.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.flush()

    assert await repo.try_acquire_lock(
        tenant_id,
        student_id,
        exam_id,
        correlation_id="third",
        ttl_seconds=60,
    )


@pytest.mark.asyncio
async def test_projection_revision_increments_on_partial_update(db_session) -> None:
    repo = SqlAlchemyTwinProjectionRepository(db_session)
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    now = datetime.now(UTC)

    from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
    from prepos.domain.twin.snapshot_entities import PreparationTwin

    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("70"),
        average_mastery=Decimal("70"),
        average_retention=Decimal("70"),
        average_confidence=Decimal("70"),
        rated_node_count=1,
        due_revision_count=0,
        high_risk_concept_count=0,
        largest_positive_driver="knowledge",
        largest_negative_driver="coverage",
        recommendation_count=0,
        last_recommendation_at=None,
        twin_payload={"profile_version": TWIN_PROFILE_V1, "readiness": {"overall_score": 70.0}},
        generated_at=now,
    )
    first = await repo.persist_partial_projection(twin)
    second = await repo.persist_partial_projection(
        PreparationTwin(
            **{
                **first.__dict__,
                "twin_payload": merge_twin_payload_sections(
                    first.twin_payload,
                    revision_queue={"due_revision_count": 1, "high_risk_concept_count": 0},
                ),
            }
        )
    )

    assert first.projection_revision == 1
    assert second.projection_revision == 2


@pytest.mark.asyncio
async def test_is_stale_learning_graph_event(db_session) -> None:
    repo = SqlAlchemyTwinProjectionRepository(db_session)
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"

    assert not await repo.is_stale_learning_graph_event(tenant_id, student_id, exam_id, "concept-a", 2)
    from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
    from prepos.domain.twin.snapshot_entities import PreparationTwin

    await repo.persist_partial_projection(
        PreparationTwin(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=None,
            average_mastery=None,
            average_retention=None,
            average_confidence=None,
            rated_node_count=0,
            due_revision_count=0,
            high_risk_concept_count=0,
            largest_positive_driver=None,
            largest_negative_driver=None,
            recommendation_count=0,
            last_recommendation_at=None,
            twin_payload={"profile_version": TWIN_PROFILE_V1},
            generated_at=datetime.now(UTC),
        ),
        learning_graph_node_version=("concept-a", 3),
    )

    assert await repo.is_stale_learning_graph_event(tenant_id, student_id, exam_id, "concept-a", 2)
    assert not await repo.is_stale_learning_graph_event(tenant_id, student_id, exam_id, "concept-a", 4)
