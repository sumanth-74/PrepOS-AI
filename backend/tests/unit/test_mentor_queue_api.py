from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from prepos.application.mentor.mentor_case_read_service import MentorQueueReadService
from prepos.domain.mentor.case_management_v1 import MentorCase
from prepos.domain.mentor.mentor_case_entities import MentorCaseQueueEntry
from prepos.domain.mentor.mentor_types_v1 import (
    CasePriority,
    CaseStatus,
    EscalationLevel,
    MentorActionType,
)


@pytest.mark.asyncio
async def test_list_queue_returns_case_fields() -> None:
    tenant_id = uuid4()
    opened_at = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    case = MentorCase(
        case_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        status=CaseStatus.OPEN,
        priority=CasePriority.HIGH,
        mentor_action_type=MentorActionType.CONTACT_STUDENT,
        escalation_level=EscalationLevel.HIGH,
        mentor_action_priority=Decimal("82.50"),
        opened_at=opened_at,
    )

    class _Repo:
        async def list_queue(
            self,
            tenant_id_arg: UUID,
            *,
            limit: int = 50,
        ) -> tuple[MentorCaseQueueEntry, ...]:
            assert tenant_id_arg == tenant_id
            return (MentorCaseQueueEntry(case=case, tenant_id=tenant_id),)

    service = MentorQueueReadService(case_repo=_Repo())  # type: ignore[arg-type]
    response = await service.list_queue(tenant_id=tenant_id)
    assert len(response.items) == 1
    item = response.items[0]
    assert item.case_id == case.case_id
    assert item.case_status == "OPEN"
    assert item.opened_at == opened_at
    assert item.priority_score == Decimal("82.50")
