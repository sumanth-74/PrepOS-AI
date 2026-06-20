from __future__ import annotations

from prepos.application.copilot.dto import CopilotSourceResponse
from prepos.application.copilot.formatters import format_optional_text, format_score
from prepos.application.mentor.mentor_dto import MentorCaseResponse
from prepos.application.twin.twin_dto import TwinDashboardResponse


def _source(label: str, reference: str) -> CopilotSourceResponse:
    return CopilotSourceResponse(label=label, reference=reference)


async def handle_summarize_student(
    *,
    dashboard: TwinDashboardResponse,
    student_id: str,
) -> tuple[str, list[CopilotSourceResponse]]:
    lines = [
        f"Student summary ({student_id}):",
        f"- Readiness: {format_score(dashboard.readiness_score)}.",
        f"- Due revisions: {dashboard.due_revision_count}; high-risk concepts: {dashboard.high_risk_concept_count}.",
        f"- Recommendations pending: {dashboard.recommendation_count}.",
    ]

    if dashboard.largest_negative_driver:
        lines.append(f"- Primary risk driver: {dashboard.largest_negative_driver.replace('_', ' ')}.")
    if dashboard.consistency_score is not None:
        lines.append(f"- Consistency score: {format_score(dashboard.consistency_score)}.")
    if dashboard.mentor_status:
        lines.append(f"- Mentor status: {dashboard.mentor_status.replace('_', ' ')}.")
    if dashboard.top_mentor_message:
        lines.append(f"- Key mentor signal: {dashboard.top_mentor_message}")

    if dashboard.goal_summary and dashboard.goal_summary.target_date:
        target = format_score(dashboard.goal_summary.target_readiness_score)
        lines.append(
            f"- Goal: readiness {target} by {dashboard.goal_summary.target_date.isoformat()}."
        )

    return "\n".join(lines), [
        _source("Twin dashboard", "GET /twin/dashboard"),
        _source("Learning graph summary", "GET /learning-graph/summary"),
    ]


async def handle_escalation_reason(
    *,
    dashboard: TwinDashboardResponse,
    mentor_case: MentorCaseResponse | None,
) -> tuple[str, list[CopilotSourceResponse]]:
    lines = ["Escalation context:"]

    if mentor_case is not None:
        lines.extend(
            [
                f"- Case status: {mentor_case.status}.",
                f"- Mentor action: {mentor_case.mentor_action_type.replace('_', ' ')}.",
                f"- Escalation level: {mentor_case.escalation_level}.",
                f"- Priority score: {format_score(mentor_case.mentor_action_priority)}.",
                f"- Opened: {mentor_case.opened_at.isoformat()}.",
            ]
        )
    elif dashboard.escalation_level:
        lines.append(f"- Escalation level: {dashboard.escalation_level}.")
        if dashboard.mentor_action:
            lines.append(f"- Recommended action: {dashboard.mentor_action.replace('_', ' ')}.")
    else:
        lines.append("- No active escalation detected for this student.")

    message = format_optional_text(dashboard.top_mentor_message, fallback="")
    if message:
        lines.append(f"- Mentor message: {message}")

    if dashboard.largest_negative_driver:
        lines.append(f"- Contributing driver: {dashboard.largest_negative_driver.replace('_', ' ')}.")

    sources = [_source("Twin dashboard", "GET /twin/dashboard")]
    if mentor_case is not None:
        sources.append(_source("Mentor case", "GET /mentor/cases/{case_id}"))
    return "\n".join(lines), sources


async def handle_top_risks(
    *,
    dashboard: TwinDashboardResponse,
) -> tuple[str, list[CopilotSourceResponse]]:
    lines = ["Top risks for this student:"]

    if dashboard.top_negative_drivers:
        for index, driver in enumerate(dashboard.top_negative_drivers[:5], start=1):
            lines.append(f"{index}. {driver.replace('_', ' ')}.")
    elif dashboard.largest_negative_driver:
        lines.append(f"1. {dashboard.largest_negative_driver.replace('_', ' ')}.")
    else:
        lines.append("- No negative drivers recorded yet.")

    if dashboard.high_risk_concept_count > 0:
        lines.append(f"- {dashboard.high_risk_concept_count} high-risk concept(s) in the learning graph.")
    if dashboard.due_revision_count > 0:
        lines.append(f"- {dashboard.due_revision_count} overdue revision(s).")
    if dashboard.risk_level:
        lines.append(f"- Predicted outcome risk level: {dashboard.risk_level}.")
    if dashboard.goal_likelihood and dashboard.goal_likelihood.lower() in {"low", "unlikely"}:
        lines.append(f"- Goal likelihood: {dashboard.goal_likelihood}.")

    return "\n".join(lines), [
        _source("Twin dashboard", "GET /twin/dashboard"),
        _source("Learning graph weaknesses", "GET /learning-graph/weaknesses"),
    ]


async def handle_forecast_summary(
    *,
    dashboard: TwinDashboardResponse,
) -> tuple[str, list[CopilotSourceResponse]]:
    lines = ["Forecast summary:"]

    if dashboard.readiness_score is not None:
        lines.append(f"- Current readiness: {format_score(dashboard.readiness_score)}.")
    if dashboard.projected_readiness is not None:
        lines.append(f"- Projected readiness: {format_score(dashboard.projected_readiness)}.")
    if dashboard.gap_to_goal is not None:
        lines.append(f"- Gap to goal: {format_score(dashboard.gap_to_goal)} points.")
    if dashboard.on_track is not None:
        lines.append(f"- On track: {'yes' if dashboard.on_track else 'no'}.")
    if dashboard.goal_probability is not None:
        lines.append(
            f"- Goal probability: {format_score(dashboard.goal_probability)}% "
            f"({dashboard.goal_likelihood or 'n/a'})."
        )
    if dashboard.expected_score is not None:
        lines.append(
            f"- Predicted score band: {format_score(dashboard.low_score)}–"
            f"{format_score(dashboard.high_score)} (expected {format_score(dashboard.expected_score)})."
        )
    if dashboard.milestone_status:
        lines.append(f"- Milestone status: {dashboard.milestone_status.replace('_', ' ')}.")

    if len(lines) == 1:
        lines.append("- Forecast sections are not populated yet for this student.")

    return "\n".join(lines), [
        _source("Twin dashboard", "GET /twin/dashboard"),
        _source("Goals", "GET /goals"),
    ]


async def handle_draft_coaching_note(
    *,
    dashboard: TwinDashboardResponse,
    mentor_case: MentorCaseResponse | None,
) -> tuple[str, list[CopilotSourceResponse]]:
    action = format_optional_text(
        mentor_case.mentor_action_type if mentor_case else dashboard.mentor_action,
        fallback="review_progress",
    ).replace("_", " ")
    escalation = format_optional_text(
        mentor_case.escalation_level if mentor_case else dashboard.escalation_level,
        fallback="standard",
    )

    primary_concern = format_optional_text(
        dashboard.largest_negative_driver,
        fallback="general progress",
    ).replace("_", " ")
    discuss_topic = format_optional_text(
        dashboard.largest_negative_driver,
        fallback="study consistency",
    ).replace("_", " ")

    lines = [
        "DRAFT COACHING NOTE (template — review before saving)",
        "",
        f"Readiness score: {format_score(dashboard.readiness_score)}.",
        f"Primary concern: {primary_concern}.",
        f"Due revisions: {dashboard.due_revision_count}. High-risk concepts: {dashboard.high_risk_concept_count}.",
        f"Recommended mentor action: {action} (escalation: {escalation}).",
        "",
        "Suggested talking points:",
        f"1. Discuss {discuss_topic}.",
    ]

    if dashboard.due_revision_count > 0:
        lines.append(f"2. Prioritize clearing {dashboard.due_revision_count} overdue revision(s).")
    if dashboard.on_track is False:
        lines.append("3. Review goal timeline — student is currently off track.")
    elif dashboard.goal_probability is not None:
        lines.append(
            f"3. Goal probability is {format_score(dashboard.goal_probability)}% — reinforce planned study items."
        )
    else:
        lines.append("3. Confirm daily study capacity and next planned activities.")

    if dashboard.top_mentor_message:
        lines.extend(["", f"System note: {dashboard.top_mentor_message}"])

    lines.extend(["", "— End draft —"])

    sources = [_source("Twin dashboard", "GET /twin/dashboard")]
    if mentor_case is not None:
        sources.append(_source("Mentor case", "GET /mentor/cases/{case_id}"))
    return "\n".join(lines), sources
