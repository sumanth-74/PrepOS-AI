from __future__ import annotations

from prepos.domain.mentor.mentor_explanations_v1 import (
    coaching_rationale,
    insight_message,
    overall_status_key_message,
)
from prepos.domain.mentor.mentor_types_v1 import CoachingAction, InsightType, OverallStatus


def test_goal_risk_message_is_deterministic() -> None:
    assert insight_message(InsightType.GOAL_RISK) == (
        "You are currently unlikely to reach your target readiness score."
    )


def test_revision_warning_message() -> None:
    assert insight_message(InsightType.REVISION_WARNING) == (
        "Overdue revisions are slowing readiness growth."
    )


def test_coaching_rationale_complete_revisions() -> None:
    rationale = coaching_rationale(CoachingAction.COMPLETE_REVISIONS)
    assert "overdue revisions" in rationale.lower()


def test_overall_status_key_message() -> None:
    assert "Immediate action" in overall_status_key_message(OverallStatus.CRITICAL)
