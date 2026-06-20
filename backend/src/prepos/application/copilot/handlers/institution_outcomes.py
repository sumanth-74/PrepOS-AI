from __future__ import annotations

from uuid import UUID

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse
from prepos.application.institution_outcomes.outcome_explainer import (
    explain_effectiveness,
    explain_outcome,
    explain_roi,
)
from prepos.application.institution_outcomes.outcome_service import InstitutionOutcomeService

ADMIN_INSTITUTION_OUTCOME_INTENTS: frozenset[str] = frozenset(
    {
        "institution_outcomes",
        "initiative_performance",
        "best_initiatives",
        "failed_initiatives",
        "roi_summary",
        "forecast_improvements",
    }
)


async def build_admin_institution_outcome_response(
    *,
    intent: str,
    outcome_service: InstitutionOutcomeService,
    tenant_id: UUID,
) -> CopilotQueryResponse:
    outcomes = await outcome_service.get_outcomes(tenant_id=tenant_id)
    roi = await outcome_service.get_roi(tenant_id=tenant_id)
    effectiveness = await outcome_service.get_effectiveness(tenant_id=tenant_id)

    if intent == "institution_outcomes":
        lines = [
            "Institution outcomes:",
            "",
            f"- Average readiness uplift: {outcomes.average_readiness_uplift:+.1f}",
            f"- Average forecast uplift: {outcomes.average_forecast_uplift:+.1f}",
            f"- Average risk reduction: {outcomes.average_risk_reduction:+.1f}",
        ]
        for outcome in outcomes.outcomes[:3]:
            lines.append(f"- {explain_outcome(outcome)}")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Institution outcomes", reference="GET /admin/institution/outcomes")],
        )

    if intent == "initiative_performance":
        lines = ["Initiative performance:", ""]
        for item in effectiveness.items[:5]:
            lines.append(f"- {explain_effectiveness(item)}")
        if not effectiveness.items:
            lines.append("- No initiative performance data yet.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Institution ROI", reference="GET /admin/institution/roi")],
        )

    if intent == "best_initiatives":
        lines = ["Best initiatives:", ""]
        for item in roi.best_initiatives[:5]:
            lines.append(f"- {explain_roi(item)}")
        if not roi.best_initiatives:
            lines.append("- No high-ROI initiatives identified yet.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Institution ROI", reference="GET /admin/institution/roi")],
        )

    if intent == "failed_initiatives":
        lines = ["Failed initiatives:", ""]
        for item in roi.failed_initiatives[:5]:
            lines.append(f"- {explain_roi(item)}")
        if not roi.failed_initiatives:
            lines.append("- No failed initiatives flagged.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="medium",
            sources=[CopilotSourceResponse(label="Institution ROI", reference="GET /admin/institution/roi")],
        )

    if intent == "forecast_improvements":
        lines = [
            "Forecast improvements:",
            "",
            f"- Average forecast uplift: {outcomes.average_forecast_uplift:+.1f}",
        ]
        for outcome in outcomes.outcomes[:5]:
            if outcome.forecast_gain > 0:
                lines.append(
                    f"- {outcome.outcome_type}: forecast {outcome.before.forecast:.1f} → "
                    f"{outcome.after.forecast:.1f} ({outcome.forecast_gain:+.1f})"
                )
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Institution outcomes", reference="GET /admin/institution/outcomes")],
        )

    lines = [
        "ROI summary:",
        "",
        f"- Average ROI score: {roi.average_roi_score:.1f}/100",
        f"- Initiatives measured: {roi.total}",
    ]
    for item in roi.items[:3]:
        lines.append(f"- {explain_roi(item)}")
    return CopilotQueryResponse(
        intent="roi_summary",
        answer="\n".join(lines),
        confidence="high",
        sources=[CopilotSourceResponse(label="Institution ROI", reference="GET /admin/institution/roi")],
    )
