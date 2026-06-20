from __future__ import annotations

from uuid import UUID

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse
from prepos.application.interventions.intervention_service import MentorInterventionService

MENTOR_INTERVENTION_OPT_INTENTS: frozenset[str] = frozenset(
    {
        "recommended_interventions",
        "highest_impact_intervention",
        "student_recovery_plan",
        "forecast_recovery",
        "coaching_priorities",
        "failed_interventions",
        "successful_interventions",
    }
)

STUDENT_INTERVENTION_INTENTS: frozenset[str] = frozenset(
    {
        "why_did_mentor_assign_this",
        "intervention_history",
        "intervention_progress",
    }
)

ADMIN_INTERVENTION_INTENTS: frozenset[str] = frozenset(
    {
        "intervention_summary",
        "intervention_effectiveness",
        "mentor_performance",
    }
)

MENTOR_INTERVENTION_INTROS: dict[str, str] = {
    "recommended_interventions": "Recommended mentor interventions:",
    "highest_impact_intervention": "Highest-impact interventions:",
    "student_recovery_plan": "Student recovery plan:",
    "forecast_recovery": "Forecast recovery interventions:",
    "coaching_priorities": "Coaching priorities:",
    "failed_interventions": "Interventions that underperformed:",
    "successful_interventions": "Successful interventions:",
}


async def build_mentor_intervention_response(
    *,
    intent: str,
    intervention_service: MentorInterventionService,
    tenant_id: UUID,
    mentor_id: UUID,
    student_user_id: UUID,
    student_id: UUID,
    exam_id: str | None,
) -> CopilotQueryResponse:
    resolved_exam = exam_id or "upsc_cse"
    bundle = await intervention_service.get_student_interventions(
        tenant_id=tenant_id,
        student_id=student_id,
        student_user_id=student_user_id,
        exam_id=resolved_exam,
    )

    if intent == "failed_interventions":
        failed = await intervention_service.get_failed_interventions(
            tenant_id=tenant_id,
            student_id=student_id,
            limit=5,
        )
        lines = [MENTOR_INTERVENTION_INTROS[intent], ""]
        if failed:
            for item in failed:
                lines.append(
                    f"- {item.intervention_type.replace('_', ' ')}"
                    f"{f' ({item.concept})' if item.concept else ''}: "
                    f"effectiveness {item.effectiveness_score:.0f}%"
                )
        else:
            lines.append("No failed interventions recorded yet.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="medium",
            sources=[CopilotSourceResponse(label="Intervention history", reference="GET /interventions/student/{student_id}")],
        )

    if intent == "successful_interventions":
        successful = await intervention_service.get_successful_interventions(
            tenant_id=tenant_id,
            student_id=student_id,
            limit=5,
        )
        lines = [MENTOR_INTERVENTION_INTROS[intent], ""]
        if successful:
            for item in successful:
                lines.append(
                    f"- {item.intervention_type.replace('_', ' ')}"
                    f"{f' ({item.concept})' if item.concept else ''}: "
                    f"+{item.actual_gain:.1f} readiness ({item.effectiveness_score:.0f}% effective)"
                )
        else:
            lines.append("No completed successful interventions yet.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="medium",
            sources=[CopilotSourceResponse(label="Intervention effectiveness", reference="GET /admin/interventions")],
        )

    if intent in {"forecast_recovery", "student_recovery_plan"}:
        recovery = [
            item
            for item in bundle.recommended_interventions
            if item.intervention_type in {"forecast_recovery_plan", "study_plan_adjustment", "goal_reset"}
        ]
        items = recovery or bundle.recommended_interventions[:3]
        lines = [MENTOR_INTERVENTION_INTROS[intent], ""]
        for item in items:
            lines.append(
                f"- {item.intervention_type.replace('_', ' ')}"
                f"{f' on {item.concept}' if item.concept else ''}: "
                f"+{item.predicted_gain:.1f} readiness (priority {item.priority_score:.0f})"
            )
        if bundle.forecast_status:
            lines.append(f"Forecast status: {bundle.forecast_status.replace('_', ' ')}.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Intervention optimizer", reference="POST /interventions/student/{student_id}/generate")],
        )

    if intent == "coaching_priorities":
        lines = [MENTOR_INTERVENTION_INTROS[intent], ""]
        for item in bundle.recommended_interventions[:3]:
            lines.append(f"- {item.reason} (+{item.predicted_gain:.1f} readiness).")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Coaching priorities", reference="GET /interventions/student/{student_id}")],
        )

    lines = [MENTOR_INTERVENTION_INTROS.get(intent, "Interventions:"), ""]
    for item in bundle.recommended_interventions[:5]:
        label = item.concept or item.intervention_type.replace("_", " ")
        lines.append(
            f"- {label}: +{item.predicted_gain:.1f} readiness, priority {item.priority_score:.0f} — {item.reason}"
        )
    return CopilotQueryResponse(
        intent=intent,
        answer="\n".join(lines),
        confidence="high",
        sources=[CopilotSourceResponse(label="Intervention recommendations", reference="GET /interventions/student/{student_id}")],
    )


async def build_student_intervention_response(
    *,
    intent: str,
    intervention_service: MentorInterventionService,
    tenant_id: UUID,
    student_user_id: UUID,
    exam_id: str | None,
) -> CopilotQueryResponse:
    resolved_exam = exam_id or "upsc_cse"
    history = await intervention_service.get_student_history(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        exam_id=resolved_exam,
        limit=10,
    )

    if intent == "intervention_history":
        lines = ["Your intervention history:", ""]
        if history.interventions:
            for item in history.interventions:
                gain = f", actual +{item.actual_gain:.1f}" if item.actual_gain is not None else ""
                lines.append(
                    f"- {item.intervention_type.replace('_', ' ')}"
                    f"{f' ({item.concept})' if item.concept else ''}: {item.status}{gain}"
                )
        else:
            lines.append("No mentor interventions recorded yet.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="medium",
            sources=[CopilotSourceResponse(label="Intervention history", reference="GET /interventions/my-history")],
        )

    if intent == "intervention_progress":
        active = [item for item in history.interventions if item.status in {"pending", "in_progress"}]
        lines = ["Intervention progress:", ""]
        if active:
            for item in active:
                lines.append(
                    f"- {item.intervention_type.replace('_', ' ')}"
                    f"{f' ({item.concept})' if item.concept else ''}: {item.status}, "
                    f"expected +{item.predicted_gain:.1f} readiness"
                )
        else:
            lines.append("No active interventions right now.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="medium",
            sources=[CopilotSourceResponse(label="Active interventions", reference="GET /interventions/my-history")],
        )

    latest = history.interventions[0] if history.interventions else None
    if latest is None:
        answer = "No mentor intervention has been assigned yet."
    else:
        answer = (
            f"Your mentor assigned {latest.intervention_type.replace('_', ' ')}"
            f"{f' for {latest.concept}' if latest.concept else ''} "
            f"with expected +{latest.predicted_gain:.1f} readiness gain. "
            f"Current status: {latest.status}."
        )
    return CopilotQueryResponse(
        intent="why_did_mentor_assign_this",
        answer=answer,
        confidence="medium" if latest else "low",
        sources=[CopilotSourceResponse(label="Latest intervention", reference="GET /interventions/my-history")],
    )


async def build_admin_intervention_response(
    *,
    intent: str,
    intervention_service: MentorInterventionService,
    tenant_id: UUID,
) -> CopilotQueryResponse:
    dashboard = await intervention_service.get_admin_dashboard(tenant_id=tenant_id)

    if intent == "intervention_effectiveness":
        lines = [
            "Intervention effectiveness summary:",
            "",
            f"- Average gain: +{dashboard.average_gain:.1f} readiness.",
            f"- Average effectiveness score: {dashboard.average_effectiveness:.1f}%.",
            f"- Mentor success rate: {dashboard.mentor_success_rate * 100:.1f}%.",
        ]
        if dashboard.least_effective_interventions:
            lines.append("- Least effective types:")
            for item in dashboard.least_effective_interventions[:3]:
                lines.append(
                    f"  • {item['intervention_type']}: {float(item['average_effectiveness']):.1f}% avg effectiveness"
                )
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Intervention analytics", reference="GET /admin/interventions")],
        )

    if intent == "mentor_performance":
        lines = [
            "Mentor intervention performance:",
            "",
            f"- Interventions (30d): {dashboard.interventions_last_30_days}.",
            f"- Success rate: {dashboard.mentor_success_rate * 100:.1f}%.",
            f"- Average gain: +{dashboard.average_gain:.1f}.",
        ]
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Mentor performance", reference="GET /admin/interventions")],
        )

    lines = [
        "Intervention summary:",
        "",
        f"- Total interventions: {dashboard.total_interventions}.",
        f"- Generated in last 30 days: {dashboard.interventions_last_30_days}.",
        f"- Average effectiveness: {dashboard.average_effectiveness:.1f}%.",
    ]
    if dashboard.top_interventions:
        lines.append("- Top intervention types:")
        for item in dashboard.top_interventions[:5]:
            lines.append(f"  • {item['intervention_type']}: {item['count']}")
    return CopilotQueryResponse(
        intent="intervention_summary",
        answer="\n".join(lines),
        confidence="high",
        sources=[CopilotSourceResponse(label="Intervention summary", reference="GET /admin/interventions")],
    )
