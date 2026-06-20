from __future__ import annotations

from uuid import UUID

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse
from prepos.application.institution.institution_explainer import (
    explain_insight,
    explain_recommendation,
)
from prepos.application.institution.institution_service import InstitutionIntelligenceService

ADMIN_INSTITUTION_INTENTS: frozenset[str] = frozenset(
    {
        "institution_summary",
        "institution_risks",
        "institution_recommendations",
        "institution_mentor_effectiveness",
        "weakest_concepts",
        "cohort_comparison",
        "forecast_trends",
        "institution_intervention_roi",
    }
)


async def build_admin_institution_response(
    *,
    intent: str,
    institution_service: InstitutionIntelligenceService,
    tenant_id: UUID,
) -> CopilotQueryResponse:
    dashboard = await institution_service.get_dashboard(tenant_id=tenant_id)
    insights = await institution_service.get_insights(tenant_id=tenant_id)
    recommendations = await institution_service.get_recommendations(tenant_id=tenant_id)
    trends = await institution_service.get_trends(tenant_id=tenant_id)
    mentors = await institution_service.get_mentor_effectiveness(tenant_id=tenant_id)

    if intent == "institution_summary":
        lines = [
            "Institution summary:",
            "",
            f"- Health score: {dashboard.kpis.institution_health_score:.1f}/100",
            f"- Students: {dashboard.kpis.total_students} across {dashboard.kpis.total_cohorts} cohorts",
            f"- Average readiness: {dashboard.kpis.average_readiness:.1f}",
            f"- Average forecast: {dashboard.kpis.average_forecast:.1f}%",
            f"- At-risk students: {dashboard.kpis.at_risk_students}",
            f"- Intervention ROI: {dashboard.kpis.intervention_roi:.1f}%",
        ]
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Institution dashboard", reference="GET /admin/institution")],
        )

    if intent == "institution_risks":
        lines = ["Institution risks:", ""]
        for insight in insights.insights[:5]:
            lines.append(f"- [{insight.severity}] {explain_insight(insight)}")
        if not insights.insights:
            lines.append("- No critical institution risks flagged.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Institution insights", reference="GET /admin/institution/insights")],
        )

    if intent == "institution_recommendations":
        lines = ["Institution recommendations:", ""]
        for recommendation in recommendations.recommendations[:5]:
            lines.append(f"- {explain_recommendation(recommendation)}")
        if not recommendations.recommendations:
            lines.append("- No recommendations generated yet.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[
                CopilotSourceResponse(
                    label="Institution recommendations",
                    reference="GET /admin/institution/recommendations",
                )
            ],
        )

    if intent == "institution_mentor_effectiveness":
        lines = ["Mentor effectiveness:", ""]
        for mentor in mentors.mentors[:5]:
            lines.append(
                f"- Mentor {mentor.mentor_id[:8]}…: "
                f"{mentor.intervention_success_rate * 100:.1f}% success, "
                f"+{mentor.average_gain:.1f} avg gain "
                f"({mentor.outperformance_pct:+.1f}% vs cohort avg)"
            )
        if not mentors.mentors:
            lines.append("- No mentor effectiveness data yet.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="medium",
            sources=[
                CopilotSourceResponse(
                    label="Mentor effectiveness",
                    reference="GET /admin/institution/mentor-effectiveness",
                )
            ],
        )

    if intent == "weakest_concepts":
        concepts = dashboard.weak_concepts or [
            insight.insight_key
            for insight in insights.insights
            if insight.insight_type == "concept_weakness"
        ]
        answer = "Weakest concepts across cohorts: " + (", ".join(concepts) if concepts else "none flagged yet.")
        return CopilotQueryResponse(
            intent=intent,
            answer=answer,
            confidence="high",
            sources=[CopilotSourceResponse(label="Institution dashboard", reference="GET /admin/institution")],
        )

    if intent == "cohort_comparison":
        lines = ["Cohort comparison:", ""]
        for cohort in dashboard.cohort_comparisons[:5]:
            lines.append(
                f"- {cohort.cohort_id}: readiness {cohort.average_readiness:.1f}, "
                f"forecast {cohort.average_forecast:.1f}%, health {cohort.cohort_health_score:.1f}, "
                f"{cohort.at_risk_count} at risk"
            )
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines) if dashboard.cohort_comparisons else "No cohort data available.",
            confidence="high",
            sources=[CopilotSourceResponse(label="Institution dashboard", reference="GET /admin/institution")],
        )

    if intent == "forecast_trends":
        lines = [
            "Forecast trends:",
            "",
            f"- Forecast trend: {trends.forecast_trend}",
            f"- Readiness trend: {trends.readiness_trend}",
        ]
        for trend in trends.trends:
            if trend.trend_type == "forecast":
                lines.append(f"- {trend.label}: {trend.trend_direction} ({trend.delta_value:+.1f})")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Institution trends", reference="GET /admin/institution/trends")],
        )

    roi = dashboard.kpis.intervention_roi
    lines = [
        "Intervention ROI:",
        "",
        f"- Institution intervention ROI: {roi:.1f}%",
        f"- At-risk students: {dashboard.kpis.at_risk_students}",
    ]
    for recommendation in recommendations.recommendations:
        if recommendation.recommendation_type in {
            "launch_intervention_program",
            "review_intervention_strategy",
        }:
            lines.append(f"- Recommendation: {recommendation.title}")
    return CopilotQueryResponse(
        intent="institution_intervention_roi",
        answer="\n".join(lines),
        confidence="high",
        sources=[CopilotSourceResponse(label="Institution dashboard", reference="GET /admin/institution")],
    )
