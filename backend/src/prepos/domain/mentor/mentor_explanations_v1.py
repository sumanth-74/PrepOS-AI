from __future__ import annotations

from prepos.domain.mentor.mentor_types_v1 import CoachingAction, InsightType, OverallStatus

MENTOR_EXPLANATIONS_V1 = "mentor_explanations_v1"


def insight_title(insight_type: InsightType) -> str:
    titles = {
        InsightType.READINESS_ALERT: "Readiness needs attention",
        InsightType.GOAL_RISK: "Goal achievement at risk",
        InsightType.REVISION_WARNING: "Overdue revisions detected",
        InsightType.BEHAVIOR_WARNING: "Study behavior needs adjustment",
        InsightType.OPTIMIZATION_OPPORTUNITY: "Intervention optimization available",
        InsightType.MILESTONE_ALERT: "Milestone progress behind schedule",
        InsightType.POSITIVE_PROGRESS: "Strong study momentum",
    }
    return titles[insight_type]


def insight_message(
    insight_type: InsightType,
    *,
    goal_probability: float | None = None,
    due_revision_count: int | None = None,
    consistency_score: float | None = None,
    readiness_score: float | None = None,
    best_intervention: str | None = None,
) -> str:
    if insight_type == InsightType.GOAL_RISK:
        return "You are currently unlikely to reach your target readiness score."
    if insight_type == InsightType.REVISION_WARNING:
        return "Overdue revisions are slowing readiness growth."
    if insight_type == InsightType.POSITIVE_PROGRESS:
        return "Your study consistency is accelerating readiness gains."
    if insight_type == InsightType.READINESS_ALERT:
        score_text = f"{readiness_score:.0f}" if readiness_score is not None else "current"
        return f"Overall readiness at {score_text} is below the level needed for steady progress."
    if insight_type == InsightType.MILESTONE_ALERT:
        return "You are behind the next milestone and need to close the readiness gap."
    if insight_type == InsightType.BEHAVIOR_WARNING:
        return "Recent study patterns indicate elevated preparation risk."
    if insight_type == InsightType.OPTIMIZATION_OPPORTUNITY:
        if best_intervention:
            return f"Historical outcomes suggest {best_intervention.replace('_', ' ').lower()} is your strongest lever."
        return "Historical intervention outcomes suggest a more effective coaching path is available."
    return "Review your preparation signals and adjust your plan."


def coaching_rationale(action: CoachingAction) -> str:
    rationales = {
        CoachingAction.COMPLETE_REVISIONS: (
            "Clearing overdue revisions restores retention gains and unlocks faster readiness growth."
        ),
        CoachingAction.FOCUS_WEAKNESS_RECOVERY: (
            "Weakness recovery has produced the strongest historical gains for your profile."
        ),
        CoachingAction.INCREASE_DAILY_STUDY_TIME: (
            "Additional daily capacity is required to close the gap to your goal on schedule."
        ),
        CoachingAction.MAINTAIN_CURRENT_PLAN: (
            "Your current plan alignment and execution are supporting steady progress."
        ),
    }
    return rationales[action]


def overall_status_key_message(status: OverallStatus) -> str:
    messages = {
        OverallStatus.EXCELLENT: "You are on an excellent trajectory toward your preparation goal.",
        OverallStatus.GOOD: "Your preparation is progressing well; stay focused on the current plan.",
        OverallStatus.AT_RISK: "Your goal is at risk unless you adjust study priorities soon.",
        OverallStatus.CRITICAL: "Immediate action is required to recover your preparation trajectory.",
    }
    return messages[status]
