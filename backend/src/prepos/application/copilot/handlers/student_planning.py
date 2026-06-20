from __future__ import annotations

from uuid import UUID

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotRecommendationResponse, CopilotSourceResponse
from prepos.application.planning.planning_models import AdaptivePlanResponse, PlanItemResponse
from prepos.application.planning.planning_service import AdaptivePlanningService

STUDENT_PLANNING_INTENTS: frozenset[str] = frozenset(
    {
        "generate_week_plan",
        "today_plan",
        "why_this_plan",
        "next_best_topic",
        "plan_progress",
    }
)

STUDENT_PLANNING_INTROS: dict[str, str] = {
    "generate_week_plan": "Your adaptive weekly study plan:",
    "today_plan": "Today's prioritized study plan:",
    "why_this_plan": "Why this plan was generated:",
    "next_best_topic": "Your next best topic from the adaptive plan:",
    "plan_progress": "Your plan completion progress:",
}


def _items_to_recommendations(items: list[PlanItemResponse]) -> list[CopilotRecommendationResponse]:
    return [
        CopilotRecommendationResponse(
            concept_id=item.concept_id,
            concept_name=item.concept_name,
            impact_score=item.priority_score / 10.0,
            reason_codes=[item.activity_type.lower()],
            reasons=[item.source_reason],
            estimated_readiness_gain=item.estimated_readiness_gain,
            confidence=item.confidence,
        )
        for item in items
    ]


def _format_plan_items(items: list[PlanItemResponse]) -> list[str]:
    lines: list[str] = []
    for index, item in enumerate(items[:8], start=1):
        lines.append(
            f"{index}. {item.concept_name} — priority {item.priority_score:.1f}/100, "
            f"+{item.estimated_readiness_gain:.1f} readiness, {item.estimated_minutes} min. "
            f"Why: {item.source_reason}."
        )
    return lines


def map_student_planning_to_copilot_response(
    *,
    intent: str,
    plan: AdaptivePlanResponse,
    explain_lines: list[str] | None = None,
) -> CopilotQueryResponse:
    intro = STUDENT_PLANNING_INTROS.get(intent, "Adaptive study plan:")
    lines = [intro, ""]

    if intent == "today_plan":
        target_items = plan.today_items
    elif intent == "next_best_topic":
        target_items = plan.today_items or plan.week_items[:1]
    elif intent == "plan_progress":
        all_items = plan.today_items + plan.week_items + plan.next_week_draft
        completed = sum(1 for item in all_items if item.completion_status == "completed")
        lines.append(f"Completed {completed}/{len(all_items)} planned items.")
        lines.append(f"Estimated total gain: +{plan.total_estimated_gain:.1f} readiness.")
        target_items = [item for item in all_items if item.completion_status != "completed"][:5]
    elif intent == "why_this_plan":
        lines.append(
            f"Plan generated from twin readiness ({plan.readiness_snapshot}), "
            f"forecast ({plan.forecast_snapshot}), weaknesses, PYQ, current affairs, and coaching memory."
        )
        if explain_lines:
            lines.extend(explain_lines)
        target_items = plan.week_items[:5]
    else:
        lines.append(f"Daily budget: {plan.daily_minutes_budget} minutes.")
        lines.append(f"Estimated total gain: +{plan.total_estimated_gain:.1f} readiness.")
        target_items = plan.week_items[:8]

    if intent != "plan_progress" or target_items:
        lines.extend(_format_plan_items(target_items))
    if not target_items and intent != "plan_progress":
        lines.append("Generate a plan with POST /planning/generate to unlock adaptive scheduling.")

    return CopilotQueryResponse(
        intent=intent,
        answer="\n".join(lines),
        recommendations=_items_to_recommendations(target_items),
        confidence="high" if target_items else "low",
        sources=[
            CopilotSourceResponse(label="Adaptive planning", reference="GET /planning/current"),
            CopilotSourceResponse(label="Plan explanation", reference="GET /planning/explain/{concept_id}"),
        ],
    )


async def build_student_planning_response(
    *,
    intent: str,
    planning_service: AdaptivePlanningService,
    tenant_id: UUID,
    user_id: UUID,
    student_id: UUID,
    exam_id: str | None,
) -> CopilotQueryResponse:
    resolved_exam = exam_id or "upsc_cse"
    if intent == "generate_week_plan":
        plan = await planning_service.generate_plan(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            exam_id=resolved_exam,
        )
    else:
        plan = await planning_service.get_current_plan(
            tenant_id=tenant_id,
            user_id=user_id,
            exam_id=resolved_exam,
        )
        if plan is None:
            plan = await planning_service.generate_plan(
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                exam_id=resolved_exam,
            )

    explain_lines: list[str] | None = None
    if intent == "why_this_plan" and plan.week_items:
        top = plan.week_items[0]
        explanation = await planning_service.explain_concept(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            exam_id=resolved_exam,
            concept_id=top.concept_id,
        )
        explain_lines = explanation.explanations

    return map_student_planning_to_copilot_response(
        intent=intent,
        plan=plan,
        explain_lines=explain_lines,
    )
