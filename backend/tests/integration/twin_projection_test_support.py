from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

from prepos.application.twin.projection_builder import TwinProjectionBuilder
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.domain.twin.snapshot_entities import PreparationTwin
from prepos.events.outbox.publisher import OutboxPublisher


def build_existing_twin(
    *,
    tenant_id: object | None = None,
    student_id: object | None = None,
    exam_id: str = "neet",
) -> PreparationTwin:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    return PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        student_id=student_id or uuid4(),
        exam_id=exam_id,
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("60"),
        average_mastery=Decimal("60"),
        average_retention=Decimal("55"),
        average_confidence=Decimal("65"),
        rated_node_count=5,
        due_revision_count=2,
        high_risk_concept_count=1,
        largest_positive_driver="knowledge",
        largest_negative_driver="coverage",
        recommendation_count=3,
        last_recommendation_at=now,
        twin_payload={"mentor": {"version": "mentor_v1"}},
        generated_at=now,
        mentor_status="AT_RISK",
        top_mentor_message="At risk",
    )


def build_projection_builder(
    *,
    existing: PreparationTwin,
    section_port: AsyncMock,
) -> tuple[TwinProjectionBuilder, AsyncMock]:
    projection_repo = AsyncMock()
    projection_repo.get_projection = AsyncMock(return_value=existing)
    projection_repo.persist_partial_projection = AsyncMock(side_effect=lambda twin, **kwargs: twin)
    outbox = AsyncMock(spec=OutboxPublisher)
    outbox.enqueue_twin_updated = AsyncMock()
    outbox.enqueue_twin_snapshot_updated = AsyncMock()
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
        outbox=outbox,
    )
    return builder, section_port


async def apply_section_update(
    *,
    section: TwinProjectionSection,
    port_attr: str,
    summary: object,
    existing: PreparationTwin | None = None,
) -> PreparationTwin:
    twin = existing or build_existing_twin()
    section_port = AsyncMock()
    getattr(section_port, port_attr).return_value = summary
    builder = TwinProjectionBuilder(
        readiness_port=section_port if section == TwinProjectionSection.READINESS else AsyncMock(),
        queue_port=AsyncMock(),
        recommendation_port=AsyncMock(),
        study_plan_port=AsyncMock(),
        behavior_port=AsyncMock(),
        forecast_port=section_port if section == TwinProjectionSection.FORECAST else AsyncMock(),
        predicted_score_port=AsyncMock(),
        milestone_port=AsyncMock(),
        forecast_probability_port=AsyncMock(),
        decision_port=section_port if section == TwinProjectionSection.DECISION else AsyncMock(),
        intervention_port=section_port if section == TwinProjectionSection.INTERVENTION else AsyncMock(),
        intervention_outcome_port=(
            section_port if section == TwinProjectionSection.INTERVENTION_OUTCOME else AsyncMock()
        ),
        behavior_profile_port=(
            section_port if section == TwinProjectionSection.BEHAVIOR_PROFILE else AsyncMock()
        ),
        personalization_port=(
            section_port if section == TwinProjectionSection.PERSONALIZATION else AsyncMock()
        ),
        mentor_port=section_port if section == TwinProjectionSection.MENTOR else AsyncMock(),
        mentor_action_port=AsyncMock(),
        mentor_case_port=AsyncMock(),
        mentor_effectiveness_port=AsyncMock(),
        projection_repo=AsyncMock(
            get_projection=AsyncMock(return_value=twin),
            persist_partial_projection=AsyncMock(side_effect=lambda updated, **kwargs: updated),
        ),
        outbox=AsyncMock(
            spec=OutboxPublisher,
            enqueue_twin_updated=AsyncMock(),
            enqueue_twin_snapshot_updated=AsyncMock(),
        ),
    )
    result = await builder.apply_incremental_update(
        section=section,
        tenant_id=twin.tenant_id,
        student_id=twin.student_id,
        exam_id=twin.exam_id,
        correlation_id="corr",
        causation_id="cause",
        current_time=twin.generated_at,
    )
    assert result is not None
    return result
