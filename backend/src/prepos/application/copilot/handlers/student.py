from __future__ import annotations

from prepos.application.copilot.dto import CopilotSourceResponse
from prepos.application.copilot.formatters import format_score
from prepos.application.goal.dto import GoalResponse
from prepos.application.learning_graph.dto import LearningGraphWeaknessesResponse
from prepos.application.study_plan.dto import StudyPlanResponse
from prepos.application.twin.dto import TwinRecommendationResponse
from prepos.application.twin.twin_dto import TwinDashboardResponse


def _source(label: str, reference: str) -> CopilotSourceResponse:
    return CopilotSourceResponse(label=label, reference=reference)


async def handle_readiness_low(
    *,
    dashboard: TwinDashboardResponse,
) -> tuple[str, list[CopilotSourceResponse]]:
    lines = ["Your readiness is influenced by these factors:"]

    if dashboard.readiness_score is not None:
        lines.append(f"- Current readiness score: {format_score(dashboard.readiness_score)}.")

    if dashboard.largest_negative_driver:
        lines.append(f"- Primary negative driver: {dashboard.largest_negative_driver.replace('_', ' ')}.")
    elif dashboard.top_negative_drivers:
        drivers = ", ".join(driver.replace("_", " ") for driver in dashboard.top_negative_drivers[:3])
        lines.append(f"- Negative drivers: {drivers}.")

    if dashboard.due_revision_count > 0:
        lines.append(f"- {dashboard.due_revision_count} revision(s) are due.")
    if dashboard.high_risk_concept_count > 0:
        lines.append(f"- {dashboard.high_risk_concept_count} high-risk concept(s) need attention.")

    if dashboard.skip_rate is not None and dashboard.skip_rate > 0:
        lines.append(f"- Study plan skip rate: {format_score(dashboard.skip_rate)}%.")

    if len(lines) == 1:
        lines.append("- Insufficient Twin data yet. Complete onboarding and record study activities.")

    return "\n".join(lines), [
        _source("Twin dashboard", "GET /twin/dashboard"),
        _source("Learning graph summary", "GET /learning-graph/summary"),
    ]


async def handle_study_today(
    *,
    dashboard: TwinDashboardResponse,
    study_plan: StudyPlanResponse,
    recommendations: list[TwinRecommendationResponse],
) -> tuple[str, list[CopilotSourceResponse]]:
    lines = ["Today's study focus:"]

    if study_plan.daily_plan:
        for index, item in enumerate(study_plan.daily_plan[:5], start=1):
            lines.append(
                f"{index}. {item.concept_id} — {item.activity_type.replace('_', ' ')} "
                f"({item.estimated_minutes} min, gain +{format_score(item.readiness_gain)})."
            )
            if item.adjustment_explanation:
                lines.append(f"   Reason: {item.adjustment_explanation}")
    elif recommendations:
        for index, item in enumerate(recommendations[:5], start=1):
            lines.append(
                f"{index}. {item.concept_id} — {item.recommendation_type.replace('_', ' ')} "
                f"(gain +{format_score(item.readiness_gain)})."
            )
    else:
        lines.append("- No daily plan items yet. Generate a study plan or complete onboarding.")

    if dashboard.due_revision_count > 0:
        lines.append(f"\nAlso complete {dashboard.due_revision_count} due revision(s) when possible.")

    return "\n".join(lines), [
        _source("Study plan", "GET /study-plan"),
        _source("Twin recommendations", "GET /twin/recommendations"),
        _source("Twin dashboard", "GET /twin/dashboard"),
    ]


async def handle_weakest_concepts(
    *,
    weaknesses: LearningGraphWeaknessesResponse,
) -> tuple[str, list[CopilotSourceResponse]]:
    if not weaknesses.weaknesses:
        return (
            "No rated weaknesses found yet. Record assessments or study sessions to build your learning graph.",
            [_source("Learning graph weaknesses", "GET /learning-graph/weaknesses")],
        )

    lines = ["Your weakest concepts by weakness score:"]
    for index, item in enumerate(weaknesses.weaknesses[:8], start=1):
        retention = format_score(item.retention_score) if item.retention_score is not None else "n/a"
        lines.append(
            f"{index}. {item.concept_id} — weakness {format_score(item.weakness_score)}, "
            f"mastery {format_score(item.mastery_score)}, retention {retention}, "
            f"importance {format_score(item.importance_score)}."
        )

    return "\n".join(lines), [_source("Learning graph weaknesses", "GET /learning-graph/weaknesses")]


async def handle_recommendation_why(
    *,
    recommendations: list[TwinRecommendationResponse],
) -> tuple[str, list[CopilotSourceResponse]]:
    if not recommendations:
        return (
            "No active recommendations yet. Recommendations appear after your learning graph is provisioned "
            "and activity is recorded.",
            [_source("Twin recommendations", "GET /twin/recommendations")],
        )

    top = recommendations[0]
    lines = [
        f"Top recommendation: {top.concept_id} ({top.recommendation_type.replace('_', ' ')}).",
        f"- Recommendation score: {format_score(top.recommendation_score)}.",
        f"- Expected readiness gain: +{format_score(top.readiness_gain)}.",
        f"- Weakness score: {format_score(top.weakness_score)}; importance: {format_score(top.importance_score)}.",
    ]
    if top.explanation:
        lines.append(f"- Explanation: {top.explanation}")

    if len(recommendations) > 1:
        lines.append("\nOther recommendations:")
        for item in recommendations[1:4]:
            lines.append(
                f"- {item.concept_id}: {item.recommendation_type.replace('_', ' ')} "
                f"(gain +{format_score(item.readiness_gain)})."
            )

    return "\n".join(lines), [_source("Twin recommendations", "GET /twin/recommendations")]


async def handle_goal_on_track(
    *,
    dashboard: TwinDashboardResponse,
    goal: GoalResponse | None,
) -> tuple[str, list[CopilotSourceResponse]]:
    lines: list[str] = []

    if goal is None:
        lines.append("You have not set a preparation goal yet.")
        lines.append("Set a target readiness score and date under Goals to enable forecast tracking.")
    else:
        lines.append(
            f"Goal: reach readiness {format_score(goal.target_readiness_score)} by {goal.target_date.isoformat()}."
        )
        if goal.goal_probability is not None:
            likelihood = goal.goal_likelihood or "n/a"
            lines.append(
                f"- Goal probability: {format_score(goal.goal_probability)}% ({likelihood})."
            )

    if dashboard.on_track is not None:
        status = "on track" if dashboard.on_track else "not on track"
        lines.append(f"- Forecast status: You are {status} for your goal.")
    if dashboard.projected_readiness is not None:
        lines.append(f"- Projected readiness: {format_score(dashboard.projected_readiness)}.")
    if dashboard.gap_to_goal is not None:
        lines.append(f"- Gap to goal: {format_score(dashboard.gap_to_goal)} points.")
    if dashboard.milestone_status:
        lines.append(f"- Milestone status: {dashboard.milestone_status.replace('_', ' ')}.")
    if dashboard.next_milestone_date and dashboard.next_milestone_target is not None:
        lines.append(
            f"- Next milestone: {format_score(dashboard.next_milestone_target)} by "
            f"{dashboard.next_milestone_date.isoformat()}."
        )

    if not lines:
        lines.append("Forecast data is not available yet. Complete activities to populate your Twin.")

    return "\n".join(lines), [
        _source("Goals", "GET /goals"),
        _source("Twin dashboard", "GET /twin/dashboard"),
    ]


async def handle_next_activities(
    *,
    study_plan: StudyPlanResponse,
    due_revision_count: int,
) -> tuple[str, list[CopilotSourceResponse]]:
    lines = ["Recommended next activities:"]

    if study_plan.daily_plan:
        for index, item in enumerate(study_plan.daily_plan[:5], start=1):
            lines.append(
                f"{index}. Complete {item.activity_type.replace('_', ' ')} for {item.concept_id} "
                f"({item.estimated_minutes} min)."
            )
    else:
        lines.append("- No planned study items. Visit Study Plan to generate your plan.")

    if due_revision_count > 0:
        lines.append(f"- Complete {due_revision_count} due revision session(s) from your revision queue.")

    lines.append("- Record completed activities so your learning graph and Twin stay up to date.")

    return "\n".join(lines), [
        _source("Study plan", "GET /study-plan"),
        _source("Revision queue", "GET /learning-graph/revisions/due"),
        _source("Twin dashboard", "GET /twin/dashboard"),
    ]
