from __future__ import annotations

from prepos.domain.mentor.mentor_types_v1 import EscalationLevel, MentorActionType

MENTOR_ACTION_EXPLANATIONS_V1 = "mentor_action_explanations_v1"


def explain_mentor_action_v1(*, action_type: MentorActionType) -> str:
    explanations = {
        MentorActionType.ESCALATE_RISK: "Immediate mentor intervention is recommended.",
        MentorActionType.CONTACT_STUDENT: "Student should be contacted due to declining consistency.",
        MentorActionType.SCHEDULE_REVIEW: "Schedule a milestone review to recover preparation trajectory.",
        MentorActionType.ASSIGN_REVISION_SPRINT: "Assign a revision sprint to clear overdue revision backlog.",
        MentorActionType.INCREASE_STUDY_TARGET: "Increase daily study targets to close the readiness gap.",
        MentorActionType.NO_ACTION_REQUIRED: "Current preparation trajectory does not require mentor action.",
    }
    return explanations[action_type]


def explain_escalation_v1(*, level: EscalationLevel) -> str:
    if level == EscalationLevel.CRITICAL:
        return "Escalation triggered because goal achievement probability is critically low."
    if level == EscalationLevel.HIGH:
        return "Escalation triggered because goal probability dropped below 50%."
    if level == EscalationLevel.MEDIUM:
        return "Escalation triggered because milestone progress is behind schedule."
    if level == EscalationLevel.LOW:
        return "Escalation triggered due to high-risk study behavior."
    return "No escalation required at this time."
