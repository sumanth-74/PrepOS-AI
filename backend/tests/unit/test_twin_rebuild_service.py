from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.twin.projection_builder import TwinProjectionBuilder
from prepos.application.twin.projection_ports import ReadinessSummary
from prepos.application.twin.rebuild_service import TwinRebuildService, clear_twin_rebuild_debounce
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.scoring.readiness_drivers_v1 import READINESS_DRIVERS_V1, ReadinessDriversV1
from prepos.domain.scoring.readiness_v1_1 import READINESS_V1_1, ReadinessResultV1_1
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.domain.twin.snapshot_entities import PreparationTwin
from prepos.events.outbox.publisher import OutboxPublisher


def _build_service(
    *,
    builder: AsyncMock,
    lock_acquired: bool = True,
) -> tuple[TwinRebuildService, AsyncMock, AsyncMock]:
    lock_repo = AsyncMock()
    lock_repo.try_acquire_lock = AsyncMock(return_value=lock_acquired)
    projection_repo = AsyncMock()
    projection_repo.record_projection_metric = AsyncMock()
    service = TwinRebuildService(
        builder=builder,
        lock_repo=lock_repo,
        projection_repo=projection_repo,
    )
    return service, lock_repo, projection_repo


@pytest.fixture(autouse=True)
def _reset_debounce() -> None:
    clear_twin_rebuild_debounce()


@pytest.mark.asyncio
async def test_rebuild_service_debounces_same_student_exam_in_cycle() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    now = datetime(2026, 6, 18, tzinfo=UTC)
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("70.00"),
        average_mastery=Decimal("75.00"),
        average_retention=Decimal("65.00"),
        average_confidence=Decimal("68.00"),
        rated_node_count=5,
        due_revision_count=1,
        high_risk_concept_count=1,
        largest_positive_driver="knowledge",
        largest_negative_driver="retention",
        recommendation_count=2,
        last_recommendation_at=now,
        twin_payload={"profile_version": TWIN_PROFILE_V1},
        generated_at=now,
    )

    builder = AsyncMock(spec=TwinProjectionBuilder)
    builder.apply_incremental_update = AsyncMock(return_value=twin)
    service, _, projection_repo = _build_service(builder=builder)

    first = await service.request_incremental_update(
        section=TwinProjectionSection.READINESS,
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        correlation_id="corr-1",
        causation_id="cause-1",
    )
    second = await service.request_incremental_update(
        section=TwinProjectionSection.READINESS,
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        correlation_id="corr-1",
        causation_id="cause-2",
    )

    assert first is twin
    assert second is None
    builder.apply_incremental_update.assert_awaited_once()
    projection_repo.record_projection_metric.assert_any_call(
        tenant_id,
        student_id,
        exam_id,
        skipped_rebuild_count=1,
    )


@pytest.mark.asyncio
async def test_rebuild_service_records_lock_contention() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    builder = AsyncMock(spec=TwinProjectionBuilder)
    service, lock_repo, projection_repo = _build_service(builder=builder, lock_acquired=False)

    result = await service.request_incremental_update(
        section=TwinProjectionSection.QUEUE,
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        correlation_id="corr-lock",
        causation_id="cause-lock",
    )

    assert result is None
    lock_repo.try_acquire_lock.assert_awaited_once()
    projection_repo.record_projection_metric.assert_awaited_with(
        tenant_id,
        student_id,
        exam_id,
        lock_contention_count=1,
    )


@pytest.mark.asyncio
async def test_projection_builder_emits_twin_updated() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    now = datetime(2026, 6, 18, tzinfo=UTC)

    readiness_port = AsyncMock()
    readiness_port.get_readiness_summary = AsyncMock(
        return_value=ReadinessSummary(
            snapshot=LearningGraphReadinessSnapshot(
                average_mastery=Decimal("80.00"),
                average_retention=Decimal("70.00"),
                average_confidence=Decimal("75.00"),
                rated_node_count=4,
                total_node_count=10,
            ),
            readiness_result=ReadinessResultV1_1(
                overall_score=Decimal("76.00"),
                knowledge_subscore=Decimal("80.00"),
                retention_subscore=Decimal("70.00"),
                confidence_subscore=Decimal("75.00"),
                coverage_subscore=Decimal("40.00"),
                rated_node_count=4,
                total_node_count=10,
                unrated=False,
                version=READINESS_V1_1,
            ),
            drivers=ReadinessDriversV1(
                largest_positive_driver="knowledge",
                largest_negative_driver="coverage",
                top_positive_drivers=("knowledge", "confidence"),
                top_negative_drivers=("coverage", "retention"),
                version=READINESS_DRIVERS_V1,
            ),
        )
    )
    queue_port = AsyncMock()
    recommendation_port = AsyncMock()
    projection_repo = AsyncMock()
    projection_repo.get_projection = AsyncMock(return_value=None)
    projection_repo.resolve_twin_id = AsyncMock(return_value=None)
    projection_repo.is_stale_learning_graph_event = AsyncMock(return_value=False)
    projection_repo.persist_partial_projection = AsyncMock(
        side_effect=lambda twin, **kwargs: twin,
    )
    outbox = AsyncMock(spec=OutboxPublisher)
    outbox.enqueue_twin_updated = AsyncMock()
    outbox.enqueue_twin_snapshot_updated = AsyncMock()

    builder = TwinProjectionBuilder(
        readiness_port=readiness_port,
        queue_port=queue_port,
        recommendation_port=recommendation_port,
        study_plan_port=AsyncMock(),
        behavior_port=AsyncMock(),
        forecast_port=AsyncMock(),
        predicted_score_port=AsyncMock(),
        milestone_port=AsyncMock(),
        forecast_probability_port=AsyncMock(),
        decision_port=AsyncMock(),
        intervention_port=AsyncMock(),
        intervention_outcome_port=AsyncMock(),
        behavior_profile_port=AsyncMock(),
        personalization_port=AsyncMock(),
        mentor_port=AsyncMock(),
        mentor_action_port=AsyncMock(),
        mentor_case_port=AsyncMock(),
        mentor_effectiveness_port=AsyncMock(),
        projection_repo=projection_repo,
        outbox=outbox,
    )
    result = await builder.apply_incremental_update(
        section=TwinProjectionSection.READINESS,
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        correlation_id="corr",
        causation_id="cause",
        concept_id="concept-a",
        learning_graph_row_version=3,
        current_time=now,
    )

    assert result is not None
    assert result.twin_payload["readiness"]["version"] == READINESS_V1_1
    outbox.enqueue_twin_updated.assert_awaited_once()
    outbox.enqueue_twin_snapshot_updated.assert_awaited_once()


@pytest.mark.asyncio
async def test_rebuild_service_records_metrics_on_success() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    now = datetime(2026, 6, 18, tzinfo=UTC)
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("70.00"),
        average_mastery=Decimal("75.00"),
        average_retention=Decimal("65.00"),
        average_confidence=Decimal("68.00"),
        rated_node_count=5,
        due_revision_count=1,
        high_risk_concept_count=1,
        largest_positive_driver="knowledge",
        largest_negative_driver="retention",
        recommendation_count=2,
        last_recommendation_at=now,
        twin_payload={"profile_version": TWIN_PROFILE_V1},
        generated_at=now,
    )

    builder = AsyncMock(spec=TwinProjectionBuilder)
    builder.apply_incremental_update = AsyncMock(return_value=twin)
    service, _, projection_repo = _build_service(builder=builder)

    result = await service.request_incremental_update(
        section=TwinProjectionSection.QUEUE,
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        correlation_id="corr-metrics",
        causation_id="cause-metrics",
    )

    assert result is twin
    projection_repo.record_projection_metric.assert_any_call(
        tenant_id,
        student_id,
        exam_id,
        rebuild_count=1,
        incremental_update_count=1,
    )


@pytest.mark.asyncio
async def test_request_rebuild_updates_all_sections_under_single_lock() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    now = datetime(2026, 6, 18, tzinfo=UTC)
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("70.00"),
        average_mastery=Decimal("75.00"),
        average_retention=Decimal("65.00"),
        average_confidence=Decimal("68.00"),
        rated_node_count=5,
        due_revision_count=1,
        high_risk_concept_count=1,
        largest_positive_driver="knowledge",
        largest_negative_driver="retention",
        recommendation_count=2,
        last_recommendation_at=now,
        twin_payload={"profile_version": TWIN_PROFILE_V1},
        generated_at=now,
    )

    builder = AsyncMock(spec=TwinProjectionBuilder)
    builder.apply_incremental_update = AsyncMock(return_value=twin)
    service, lock_repo, projection_repo = _build_service(builder=builder)

    result = await service.request_rebuild(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        correlation_id="corr-full",
        causation_id="cause-full",
    )

    assert result is twin
    lock_repo.try_acquire_lock.assert_awaited_once()
    assert builder.apply_incremental_update.await_count == 17
    projection_repo.record_projection_metric.assert_awaited_with(
        tenant_id,
        student_id,
        exam_id,
        rebuild_count=1,
        incremental_update_count=17,
    )


@pytest.mark.asyncio
async def test_projection_builder_skips_stale_learning_graph_event() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    projection_repo = AsyncMock()
    projection_repo.is_stale_learning_graph_event = AsyncMock(return_value=True)
    projection_repo.record_projection_metric = AsyncMock()
    builder = TwinProjectionBuilder(
        readiness_port=AsyncMock(),
        queue_port=AsyncMock(),
        recommendation_port=AsyncMock(),
        study_plan_port=AsyncMock(),
        behavior_port=AsyncMock(),
        forecast_port=AsyncMock(),
        predicted_score_port=AsyncMock(),
        milestone_port=AsyncMock(),
        forecast_probability_port=AsyncMock(),
        decision_port=AsyncMock(),
        intervention_port=AsyncMock(),
        intervention_outcome_port=AsyncMock(),
        behavior_profile_port=AsyncMock(),
        personalization_port=AsyncMock(),
        mentor_port=AsyncMock(),
        mentor_action_port=AsyncMock(),
        mentor_case_port=AsyncMock(),
        mentor_effectiveness_port=AsyncMock(),
        projection_repo=projection_repo,
        outbox=AsyncMock(),
    )

    result = await builder.apply_incremental_update(
        section=TwinProjectionSection.READINESS,
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        correlation_id="corr",
        causation_id="cause",
        concept_id="concept-a",
        learning_graph_row_version=2,
    )

    assert result is None
    projection_repo.record_projection_metric.assert_awaited_with(
        tenant_id,
        student_id,
        exam_id,
        skipped_rebuild_count=1,
    )
