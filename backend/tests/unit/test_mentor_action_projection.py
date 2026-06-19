"""Integration placeholder for mentor action projection."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.twin.projection_builder import TwinProjectionBuilder
from prepos.application.twin.projection_ports import MentorActionSummary
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.domain.twin.snapshot_entities import PreparationTwin
from prepos.events.outbox.publisher import OutboxPublisher


@pytest.mark.asyncio
async def test_mentor_action_projection_persists_action_fields() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    now = datetime(2026, 6, 18, tzinfo=UTC)
    existing = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("60"),
        average_mastery=None,
        average_retention=None,
        average_confidence=None,
        rated_node_count=0,
        due_revision_count=6,
        high_risk_concept_count=1,
        largest_positive_driver=None,
        largest_negative_driver="coverage",
        recommendation_count=0,
        last_recommendation_at=None,
        twin_payload={
            "mentor": {
                "version": "mentor_v1",
                "summary": {"overall_status": "AT_RISK"},
            }
        },
        generated_at=now,
        mentor_status="AT_RISK",
        top_mentor_message="At risk",
    )
    projection_repo = AsyncMock()
    projection_repo.get_projection = AsyncMock(return_value=existing)
    projection_repo.persist_partial_projection = AsyncMock(side_effect=lambda twin, **kwargs: twin)
    mentor_action_port = AsyncMock()
    mentor_action_port.get_mentor_action_summary = AsyncMock(
        return_value=MentorActionSummary(
            mentor_action_type="ASSIGN_REVISION_SPRINT",
            mentor_action_priority=Decimal("72.50"),
            escalation_level="HIGH",
            mentor_payload_patch={
                "mentor_action": {
                    "action_type": "ASSIGN_REVISION_SPRINT",
                    "priority_score": 72.5,
                    "urgency": "MEDIUM",
                    "expected_impact": 3.2,
                    "explanation": "Assign a revision sprint to clear overdue revision backlog.",
                },
                "escalation": {
                    "level": "HIGH",
                    "reason": "Escalation triggered because goal probability dropped below 50%.",
                },
            },
        )
    )
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
        mentor_action_port=mentor_action_port,
        mentor_case_port=AsyncMock(),
        mentor_effectiveness_port=AsyncMock(),
        projection_repo=projection_repo,
        outbox=outbox,
    )

    result = await builder.apply_incremental_update(
        section=TwinProjectionSection.MENTOR_ACTION,
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        correlation_id="corr",
        causation_id="cause",
        current_time=now,
    )

    assert result is not None
    assert result.mentor_action_type == "ASSIGN_REVISION_SPRINT"
    assert result.mentor_action_priority == Decimal("72.50")
    assert result.escalation_level == "HIGH"
    mentor_payload = result.twin_payload["mentor"]
    assert isinstance(mentor_payload, dict)
    assert mentor_payload["mentor_action"]["action_type"] == "ASSIGN_REVISION_SPRINT"
    assert mentor_payload["escalation"]["level"] == "HIGH"
