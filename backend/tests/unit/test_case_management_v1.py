from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.domain.mentor.case_management_v1 import (
    map_case_priority,
    should_create_case,
)
from prepos.domain.mentor.mentor_types_v1 import (
    CASE_CREATING_ACTIONS,
    ActionUrgency,
    CasePriority,
    EscalationLevel,
    MentorActionType,
)


def test_case_creating_actions() -> None:
    assert MentorActionType.ESCALATE_RISK in CASE_CREATING_ACTIONS
    assert MentorActionType.CONTACT_STUDENT in CASE_CREATING_ACTIONS
    assert MentorActionType.SCHEDULE_REVIEW in CASE_CREATING_ACTIONS
    assert MentorActionType.ASSIGN_REVISION_SPRINT not in CASE_CREATING_ACTIONS
    assert MentorActionType.NO_ACTION_REQUIRED not in CASE_CREATING_ACTIONS


def test_should_create_case_only_for_actionable_types() -> None:
    assert should_create_case(action_type=MentorActionType.ESCALATE_RISK) is True
    assert should_create_case(action_type=MentorActionType.ASSIGN_REVISION_SPRINT) is False
    assert should_create_case(action_type=MentorActionType.INCREASE_STUDY_TARGET) is False


def test_map_case_priority_from_escalation_and_urgency() -> None:
    assert (
        map_case_priority(
            urgency=ActionUrgency.HIGH,
            escalation_level=EscalationLevel.CRITICAL,
        )
        == CasePriority.CRITICAL
    )
    assert (
        map_case_priority(
            urgency=ActionUrgency.LOW,
            escalation_level=EscalationLevel.NONE,
        )
        == CasePriority.LOW
    )
