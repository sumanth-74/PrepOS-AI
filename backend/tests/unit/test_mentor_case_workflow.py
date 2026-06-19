from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.mentor.mentor_case_service import MentorCaseService
from prepos.domain.mentor.case_management_v1 import MentorCase
from prepos.domain.mentor.mentor_types_v1 import (
    ActionUrgency,
    CasePriority,
    CaseStatus,
    EscalationLevel,
    MentorActionType,
)
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.snapshot_entities import PreparationTwin


@pytest.mark.asyncio
async def test_process_mentor_action_updated_creates_case() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    now = datetime(2026, 6, 18, tzinfo=UTC)
    case = MentorCase(
        case_id=uuid4(),
        student_id=student_id,
        exam_id=exam_id,
        status=CaseStatus.OPEN,
        priority=CasePriority.HIGH,
        mentor_action_type=MentorActionType.ESCALATE_RISK,
        escalation_level=EscalationLevel.HIGH,
        mentor_action_priority=Decimal("85.00"),
        opened_at=now,
    )
    case_repo = AsyncMock()
    case_repo.get_open_case = AsyncMock(return_value=None)
    case_repo.create_case = AsyncMock(return_value=case)
    projection_repo = AsyncMock()
    projection_repo.get_projection = AsyncMock(
        return_value=PreparationTwin(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=Decimal("50"),
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
            twin_payload={},
            generated_at=now,
            escalation_level="HIGH",
        )
    )
    outbox = AsyncMock()
    outbox.enqueue_mentor_case_created = AsyncMock()
    service = MentorCaseService(
        case_repo=case_repo,
        projection_repo=projection_repo,
        outbox=outbox,
    )

    result = await service.process_mentor_action_updated(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        action_type=MentorActionType.ESCALATE_RISK,
        priority_score=Decimal("85.00"),
        urgency=ActionUrgency.HIGH,
        correlation_id="corr",
        causation_id="cause",
        current_time=now,
    )

    assert result is not None
    case_repo.create_case.assert_awaited_once()
    outbox.enqueue_mentor_case_created.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_mentor_action_updated_skips_non_case_actions() -> None:
    service = MentorCaseService(
        case_repo=AsyncMock(),
        projection_repo=AsyncMock(),
        outbox=AsyncMock(),
    )
    result = await service.process_mentor_action_updated(
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        action_type=MentorActionType.NO_ACTION_REQUIRED,
        priority_score=Decimal("0"),
        urgency=ActionUrgency.LOW,
        correlation_id="corr",
        causation_id="cause",
    )
    assert result is None
