from __future__ import annotations

from decimal import Decimal

from prepos.domain.mentor.mentor_types_v1 import CaseResolutionReason, MentorActionType

MENTOR_CASE_EXPLANATIONS_V1 = "mentor_case_explanations_v1"


def explain_case_opened_v1(*, action_type: MentorActionType) -> str:
    explanations = {
        MentorActionType.ESCALATE_RISK: (
            "Student was contacted after goal probability fell below 40%."
        ),
        MentorActionType.CONTACT_STUDENT: (
            "Case opened because the student exhibits high-risk study behavior."
        ),
        MentorActionType.SCHEDULE_REVIEW: (
            "Case opened because milestone progress is behind schedule."
        ),
    }
    return explanations.get(
        action_type,
        "Mentor case opened due to actionable preparation risk signals.",
    )


def explain_case_resolved_v1(
    *,
    reason: CaseResolutionReason,
    readiness_delta: Decimal | None = None,
) -> str:
    if reason == CaseResolutionReason.RISK_REDUCED and readiness_delta is not None:
        return f"Case resolved after readiness improved by {readiness_delta} points."
    explanations = {
        CaseResolutionReason.STUDENT_CONTACTED: "Case resolved after the student was contacted.",
        CaseResolutionReason.PLAN_UPDATED: "Case resolved after the study plan was updated.",
        CaseResolutionReason.RISK_REDUCED: "Case resolved after preparation risk was reduced.",
        CaseResolutionReason.GOAL_ADJUSTED: "Case resolved after the preparation goal was adjusted.",
        CaseResolutionReason.FALSE_POSITIVE: "Case closed as a false-positive risk signal.",
    }
    return explanations[reason]
