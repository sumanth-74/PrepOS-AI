from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from prepos.application.mentor.mentor_case_read_service import MentorCaseReadService
from prepos.domain.mentor.case_management_v1 import MentorCase, MentorCaseNote
from prepos.domain.mentor.mentor_types_v1 import (
    CasePriority,
    CaseStatus,
    EscalationLevel,
    MentorActionType,
)
from decimal import Decimal


@pytest.mark.asyncio
async def test_get_case_returns_notes() -> None:
    tenant_id = uuid4()
    case_id = uuid4()
    mentor_id = uuid4()
    opened_at = datetime(2026, 6, 18, tzinfo=UTC)
    case = MentorCase(
        case_id=case_id,
        student_id=uuid4(),
        exam_id="neet",
        status=CaseStatus.OPEN,
        priority=CasePriority.HIGH,
        mentor_action_type=MentorActionType.CONTACT_STUDENT,
        escalation_level=EscalationLevel.HIGH,
        mentor_action_priority=Decimal("80"),
        opened_at=opened_at,
    )
    note = MentorCaseNote(
        id=uuid4(),
        case_id=case_id,
        mentor_id=mentor_id,
        note="Follow up with student.",
        created_at=opened_at,
    )

    class _Repo:
        async def get_case(self, tenant_id_arg: UUID, case_id_arg: UUID) -> MentorCase | None:
            assert tenant_id_arg == tenant_id
            assert case_id_arg == case_id
            return case

        async def list_notes(
            self,
            tenant_id_arg: UUID,
            case_id_arg: UUID,
        ) -> tuple[MentorCaseNote, ...]:
            return (note,)

    service = MentorCaseReadService(case_repo=_Repo())  # type: ignore[arg-type]
    response = await service.get_case(tenant_id=tenant_id, case_id=case_id)
    assert response.case_id == case_id
    assert len(response.notes) == 1
    assert response.notes[0].note == "Follow up with student."
