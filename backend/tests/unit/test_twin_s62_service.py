from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.learning_graph.dto import LearningGraphReadinessSnapshotResponse
from prepos.application.twin.projection_ports import RecommendationSummary
from prepos.application.twin.services import TwinRecommendationService
from prepos.domain.learning_graph.entities import ConceptProgressNode
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.twin.entities import PersistedTwinRecommendation, TwinRecommendation


def _node(*, concept_id: str) -> ConceptProgressNode:
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
        mastery_score=Decimal("40"),
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


@pytest.mark.asyncio
async def test_recompute_recommendation_for_concept_upserts_single_row() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    concept_id = "concept-a"
    node = _node(concept_id=concept_id)

    read_service = AsyncMock()
    read_service.get_progress_node = AsyncMock(return_value=node)
    read_service.get_readiness_snapshot = AsyncMock(
        return_value=LearningGraphReadinessSnapshotResponse(
            student_id=student_id,
            average_mastery=Decimal("70"),
            average_retention=Decimal("70"),
            average_confidence=Decimal("70"),
            rated_node_count=1,
            total_node_count=1,
        )
    )
    read_service.list_due_revisions = AsyncMock(return_value=[])

    recommendation_repo = AsyncMock()
    recommendation_repo.get_recommendation_summary = AsyncMock(
        return_value=RecommendationSummary(
            recommendation_count=1,
            last_recommendation_at=datetime(2026, 6, 18, tzinfo=UTC),
            top_recommendations=(
                PersistedTwinRecommendation(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    student_id=student_id,
                    exam_id=exam_id,
                    concept_id=concept_id,
                    recommendation_type="WEAKNESS_RECOVERY",
                    recommendation_score=Decimal("80"),
                    readiness_gain=Decimal("5.00"),
                    created_at=datetime(2026, 6, 18, tzinfo=UTC),
                ),
            ),
        )
    )
    outbox = AsyncMock()

    service = TwinRecommendationService(
        learning_graph_read_service=read_service,
        recommendation_repo=recommendation_repo,
        outbox=outbox,
    )

    result = await service.recompute_recommendation_for_concept(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        concept_id=concept_id,
        correlation_id="corr",
        causation_id="cause",
    )

    assert isinstance(result, TwinRecommendation)
    recommendation_repo.upsert_recommendation.assert_awaited_once()
    recommendation_repo.delete_recommendation.assert_not_awaited()
    outbox.enqueue_twin_recommendations_updated.assert_awaited_once()


@pytest.mark.asyncio
async def test_recompute_recommendation_for_concept_deletes_missing_node() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    concept_id = "concept-missing"

    read_service = AsyncMock()
    read_service.get_progress_node = AsyncMock(return_value=None)

    recommendation_repo = AsyncMock()
    recommendation_repo.get_recommendation_summary = AsyncMock(
        return_value=RecommendationSummary(
            recommendation_count=0,
            last_recommendation_at=None,
            top_recommendations=(),
        )
    )
    outbox = AsyncMock()

    service = TwinRecommendationService(
        learning_graph_read_service=read_service,
        recommendation_repo=recommendation_repo,
        outbox=outbox,
    )

    result = await service.recompute_recommendation_for_concept(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        concept_id=concept_id,
        correlation_id="corr",
        causation_id="cause",
    )

    assert result is None
    recommendation_repo.delete_recommendation.assert_awaited_once_with(
        tenant_id,
        student_id,
        exam_id,
        concept_id,
    )
    recommendation_repo.upsert_recommendation.assert_not_awaited()
