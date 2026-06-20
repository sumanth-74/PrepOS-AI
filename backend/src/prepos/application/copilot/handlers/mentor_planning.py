from __future__ import annotations

from uuid import UUID

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse
from prepos.application.copilot.handlers.student_planning import (
    _format_plan_items,
    _items_to_recommendations,
    map_student_planning_to_copilot_response,
)
from prepos.application.planning.planning_service import AdaptivePlanningService

MENTOR_PLANNING_INTENTS: frozenset[str] = frozenset(
    {
        "student_week_plan",
        "plan_adjustments",
        "plan_risk_areas",
        "recommended_interventions",
    }
)

MENTOR_PLANNING_INTROS: dict[str, str] = {
    "student_week_plan": "This student's adaptive weekly plan:",
    "plan_adjustments": "Suggested plan adjustments based on execution and outcomes:",
    "plan_risk_areas": "Plan risk areas requiring mentor attention:",
    "recommended_interventions": "Recommended mentor interventions from the adaptive plan:",
}


async def build_mentor_planning_response(
    *,
    intent: str,
    planning_service: AdaptivePlanningService,
    tenant_id: UUID,
    student_user_id: UUID,
    student_id: UUID,
    exam_id: str | None,
) -> CopilotQueryResponse:
    resolved_exam = exam_id or "upsc_cse"
    plan = await planning_service.get_current_plan(
        tenant_id=tenant_id,
        user_id=student_user_id,
        exam_id=resolved_exam,
    )
    if plan is None:
        plan = await planning_service.generate_plan(
            tenant_id=tenant_id,
            user_id=student_user_id,
            student_id=student_id,
            exam_id=resolved_exam,
        )

    if intent == "student_week_plan":
        return map_student_planning_to_copilot_response(intent=intent, plan=plan)

    if intent == "plan_adjustments":
        revisions = await planning_service.list_revisions(
            tenant_id=tenant_id,
            user_id=student_user_id,
            exam_id=resolved_exam,
        )
        lines = [MENTOR_PLANNING_INTROS[intent], ""]
        if revisions:
            for revision in revisions[:5]:
                lines.append(
                    f"- {revision.concept_id}: {revision.revision_reason} "
                    f"({revision.old_priority} → {revision.new_priority})"
                )
        else:
            pending = [item for item in plan.week_items if item.completion_status != "completed"]
            lines.append(f"- {len(pending)} items still pending this week.")
            lines.append("- Consider regenerating if readiness forecast diverges.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="medium",
            sources=[CopilotSourceResponse(label="Plan revisions", reference="GET /planning/revisions")],
        )

    if intent == "plan_risk_areas":
        low_confidence = [item for item in plan.week_items if item.confidence == "low"]
        lines = [MENTOR_PLANNING_INTROS[intent], ""]
        if low_confidence:
            lines.extend(_format_plan_items(low_confidence[:5]))
        else:
            lines.append("No high-risk plan items flagged this week.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            recommendations=_items_to_recommendations(low_confidence[:5]),
            confidence="high" if low_confidence else "medium",
            sources=[CopilotSourceResponse(label="Student plan", reference="GET /planning/student/{student_id}")],
        )

    interventions = sorted(plan.week_items, key=lambda item: -item.priority_score)[:5]
    lines = [MENTOR_PLANNING_INTROS[intent], ""]
    lines.extend(_format_plan_items(interventions))
    return CopilotQueryResponse(
        intent=intent,
        answer="\n".join(lines),
        recommendations=_items_to_recommendations(interventions),
        confidence="high",
        sources=[CopilotSourceResponse(label="Adaptive planning", reference="GET /planning/student/{student_id}")],
    )
