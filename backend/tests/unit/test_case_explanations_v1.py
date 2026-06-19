from __future__ import annotations

from decimal import Decimal

from prepos.domain.mentor.mentor_case_explanations_v1 import (
    explain_case_opened_v1,
    explain_case_resolved_v1,
)
from prepos.domain.mentor.mentor_types_v1 import CaseResolutionReason, MentorActionType


def test_explain_case_opened_is_deterministic() -> None:
    assert explain_case_opened_v1(action_type=MentorActionType.ESCALATE_RISK) == (
        "Student was contacted after goal probability fell below 40%."
    )
    assert explain_case_opened_v1(action_type=MentorActionType.SCHEDULE_REVIEW) == (
        "Case opened because milestone progress is behind schedule."
    )


def test_explain_case_resolved_is_deterministic() -> None:
    assert explain_case_resolved_v1(
        reason=CaseResolutionReason.RISK_REDUCED,
        readiness_delta=Decimal("8.2"),
    ) == "Case resolved after readiness improved by 8.2 points."
    assert explain_case_resolved_v1(reason=CaseResolutionReason.FALSE_POSITIVE) == (
        "Case closed as a false-positive risk signal."
    )
