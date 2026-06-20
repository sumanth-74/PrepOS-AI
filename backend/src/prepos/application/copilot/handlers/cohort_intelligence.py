from __future__ import annotations

from uuid import UUID

from prepos.application.cohort.cohort_models import CohortSummaryResponse
from prepos.application.cohort.cohort_risk_engine import stagnant_students, top_improvers
from prepos.application.cohort.cohort_service import CohortIntelligenceService
from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse

MENTOR_COHORT_INTENTS: frozenset[str] = frozenset(
    {
        "at_risk_students",
        "critical_students",
        "top_improvers",
        "stagnant_students",
        "cohort_summary",
        "cohort_trends",
        "mentor_effectiveness",
    }
)

ADMIN_COHORT_INTENTS: frozenset[str] = frozenset(
    {
        "institution_health",
        "cohort_health",
        "segment_distribution",
        "top_risk_areas",
        "mentor_comparison",
    }
)


async def build_mentor_cohort_response(
    *,
    intent: str,
    cohort_service: CohortIntelligenceService,
    tenant_id: UUID,
    exam_id: str | None,
) -> CopilotQueryResponse:
    resolved_exam = exam_id or "upsc_cse"
    summary = await cohort_service.get_cohort_summary(tenant_id=tenant_id, exam_id=resolved_exam)
    students_rows = await cohort_service.load_student_inputs_for_exam(
        tenant_id=tenant_id,
        exam_id=resolved_exam,
    )

    if intent == "at_risk_students":
        count = summary.segments.get("at_risk", 0) + summary.segments.get("critical_risk", 0)
        lines = [
            "At-risk students in cohort:",
            "",
            f"- At risk: {summary.segments.get('at_risk', 0)}",
            f"- Critical risk: {summary.segments.get('critical_risk', 0)}",
            f"- Total flagged: {count}",
        ]
        if summary.top_risks:
            lines.append(f"- Top concept risks: {', '.join(summary.top_risks)}.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Cohort risks", reference="GET /cohort/risks")],
        )

    if intent == "critical_students":
        count = summary.segments.get("critical_risk", 0)
        return CopilotQueryResponse(
            intent=intent,
            answer=f"Critical-risk students: {count} in cohort {summary.cohort_id}.",
            confidence="high",
            sources=[CopilotSourceResponse(label="Cohort segments", reference="GET /cohort/segments")],
        )

    if intent == "top_improvers":
        improvers = top_improvers(students_rows, limit=5)
        lines = ["Top improvers:", ""]
        for student in improvers:
            lines.append(f"- Student {str(student.student_id)[:8]}…: +{student.readiness_delta:.1f} readiness delta")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines) if improvers else "No improving students identified yet.",
            confidence="medium",
            sources=[CopilotSourceResponse(label="Cohort students", reference="GET /cohort/students")],
        )

    if intent == "stagnant_students":
        stagnant = stagnant_students(students_rows, limit=5)
        lines = ["Stagnant students:", ""]
        for student in stagnant:
            lines.append(
                f"- Student {str(student.student_id)[:8]}…: readiness {student.readiness:.1f}, "
                f"weekly progress {student.weekly_progress:.1f}"
            )
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines) if stagnant else "No stagnant students flagged.",
            confidence="medium",
            sources=[CopilotSourceResponse(label="Cohort segments", reference="GET /cohort/segments")],
        )

    if intent == "cohort_trends":
        trends = await cohort_service.get_cohort_trends(tenant_id=tenant_id, exam_id=resolved_exam)
        lines = [
            "Cohort trends:",
            "",
            f"- Readiness trend: {trends.readiness_trend}",
            f"- Forecast trend: {trends.forecast_trend}",
            f"- Cohort growth: {trends.cohort_growth * 100:.1f}%",
        ]
        for trend in trends.trends[:3]:
            lines.append(
                f"- {trend.concept_name}: {trend.trend_direction} ({trend.readiness_delta:+.1f})"
            )
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Cohort trends", reference="GET /cohort/trends")],
        )

    if intent == "mentor_effectiveness":
        admin = await cohort_service.get_admin_dashboard(tenant_id=tenant_id)
        lines = ["Mentor effectiveness:", ""]
        for mentor in admin.mentor_comparisons[:3]:
            lines.append(
                f"- Mentor {mentor.mentor_id[:8]}…: "
                f"{mentor.intervention_success_rate * 100:.1f}% success, "
                f"+{mentor.average_gain:.1f} avg gain"
            )
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines) if admin.mentor_comparisons else "No mentor effectiveness data yet.",
            confidence="medium",
            sources=[CopilotSourceResponse(label="Admin cohort", reference="GET /admin/cohort")],
        )

    return _summary_response(intent=intent, summary=summary)


async def build_admin_cohort_response(
    *,
    intent: str,
    cohort_service: CohortIntelligenceService,
    tenant_id: UUID,
) -> CopilotQueryResponse:
    admin = await cohort_service.get_admin_dashboard(tenant_id=tenant_id)
    summary = await cohort_service.get_cohort_summary(tenant_id=tenant_id, refresh=False)

    if intent in {"institution_health", "cohort_health"}:
        return CopilotQueryResponse(
            intent=intent,
            answer=(
                f"Institution cohort health: {admin.average_cohort_health:.1f}/100. "
                f"Average readiness {summary.metrics.average_readiness:.1f}, "
                f"forecast {summary.metrics.average_forecast:.1f}%. "
                f"{summary.segments.get('at_risk', 0) + summary.segments.get('critical_risk', 0)} students at risk."
            ),
            confidence="high",
            sources=[CopilotSourceResponse(label="Admin cohort", reference="GET /admin/cohort")],
        )

    if intent == "segment_distribution":
        lines = ["Segment distribution:", ""]
        for segment, count in sorted(admin.segment_distribution.items(), key=lambda p: p[1], reverse=True):
            lines.append(f"- {segment.replace('_', ' ')}: {count}")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Cohort segments", reference="GET /admin/cohort/segments")],
        )

    if intent == "top_risk_areas":
        risks = summary.top_risks or admin.top_risk_concepts
        answer = "Top risk areas: " + (", ".join(risks) if risks else "none flagged yet.")
        return CopilotQueryResponse(
            intent=intent,
            answer=answer,
            confidence="high",
            sources=[CopilotSourceResponse(label="Cohort risks", reference="GET /admin/cohort/risks")],
        )

    lines = ["Mentor comparison:", ""]
    for mentor in admin.mentor_comparisons:
        lines.append(
            f"- {mentor.mentor_id[:8]}…: success {mentor.intervention_success_rate * 100:.1f}%, "
            f"students {mentor.student_count}, gain +{mentor.average_gain:.1f}"
        )
    return CopilotQueryResponse(
        intent="mentor_comparison",
        answer="\n".join(lines) if admin.mentor_comparisons else "No mentor comparison data yet.",
        confidence="medium",
        sources=[CopilotSourceResponse(label="Admin cohort", reference="GET /admin/cohort")],
    )


def _summary_response(*, intent: str, summary: CohortSummaryResponse) -> CopilotQueryResponse:
    lines = [
        f"Cohort {summary.cohort_id}: {summary.student_count} students.",
        f"Health score {summary.metrics.cohort_health_score:.1f}/100.",
        "",
        "Segments:",
    ]
    for segment, count in sorted(summary.segments.items(), key=lambda pair: pair[1], reverse=True):
        lines.append(f"- {segment.replace('_', ' ')}: {count}")
    if summary.top_risks:
        lines.extend(["", f"Top risks: {', '.join(summary.top_risks)}."])
    return CopilotQueryResponse(
        intent=intent,
        answer="\n".join(lines),
        confidence="high",
        sources=[CopilotSourceResponse(label="Cohort summary", reference="GET /cohort/summary")],
    )
