from __future__ import annotations

from prepos.domain.mentor.mentor_action_explanations_v1 import (
    explain_escalation_v1,
    explain_mentor_action_v1,
)
from prepos.domain.mentor.mentor_types_v1 import EscalationLevel, MentorActionType


def test_explain_mentor_action_is_deterministic() -> None:
    assert explain_mentor_action_v1(action_type=MentorActionType.ESCALATE_RISK) == (
        "Immediate mentor intervention is recommended."
    )
    assert explain_mentor_action_v1(action_type=MentorActionType.CONTACT_STUDENT) == (
        "Student should be contacted due to declining consistency."
    )
    assert explain_mentor_action_v1(action_type=MentorActionType.NO_ACTION_REQUIRED) == (
        "Current preparation trajectory does not require mentor action."
    )


def test_explain_escalation_is_deterministic() -> None:
    assert explain_escalation_v1(level=EscalationLevel.CRITICAL) == (
        "Escalation triggered because goal achievement probability is critically low."
    )
    assert explain_escalation_v1(level=EscalationLevel.HIGH) == (
        "Escalation triggered because goal probability dropped below 50%."
    )
    assert explain_escalation_v1(level=EscalationLevel.NONE) == (
        "No escalation required at this time."
    )
