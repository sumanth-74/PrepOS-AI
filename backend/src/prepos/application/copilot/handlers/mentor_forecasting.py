from __future__ import annotations

from uuid import UUID

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse
from prepos.application.copilot.handlers.student_forecasting import map_student_forecast_to_copilot_response
from prepos.application.forecasting.forecast_service import GoalForecastingService

MENTOR_FORECASTING_INTENTS: frozenset[str] = frozenset(
    {
        "student_forecast",
        "intervention_impact",
        "forecast_risk",
        "goal_attainment_probability",
    }
)

MENTOR_FORECASTING_INTROS: dict[str, str] = {
    "student_forecast": "Student goal forecast:",
    "intervention_impact": "Intervention impact on forecast:",
    "forecast_risk": "Forecast risk areas:",
    "goal_attainment_probability": "Goal attainment probability:",
}


async def build_mentor_forecast_response(
    *,
    intent: str,
    forecast_service: GoalForecastingService,
    tenant_id: UUID,
    student_user_id: UUID,
    student_id: UUID,
    exam_id: str | None,
) -> CopilotQueryResponse:
    resolved_exam = exam_id or "upsc_cse"
    forecast = await forecast_service.get_current_forecast(
        tenant_id=tenant_id,
        user_id=student_user_id,
        exam_id=resolved_exam,
    )
    if forecast is None:
        forecast = await forecast_service.generate_forecast(
            tenant_id=tenant_id,
            user_id=student_user_id,
            student_id=student_id,
            exam_id=resolved_exam,
        )

    if intent == "student_forecast":
        return map_student_forecast_to_copilot_response(intent=intent, forecast=forecast)

    if intent == "forecast_risk":
        risky = [s for s in forecast.scenarios if s.probability_of_success < 60]
        lines = [MENTOR_FORECASTING_INTROS[intent], ""]
        if risky:
            for scenario in risky[:3]:
                lines.append(
                    f"- {scenario.scenario_name}: {scenario.probability_of_success:.0f}% success at "
                    f"{scenario.projected_readiness:.1f} readiness"
                )
        else:
            lines.append("No high-risk scenarios flagged in the current forecast.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="medium",
            sources=[CopilotSourceResponse(label="Student forecast", reference="GET /forecasting/student/{student_id}")],
        )

    if intent == "intervention_impact":
        stretch = next((s for s in forecast.scenarios if s.scenario_type == "stretch_plan"), None)
        baseline = next((s for s in forecast.scenarios if s.scenario_type == "baseline"), forecast.scenarios[0] if forecast.scenarios else None)
        lines = [MENTOR_FORECASTING_INTROS[intent], ""]
        if stretch and baseline:
            delta = stretch.projected_readiness - baseline.projected_readiness
            lines.append(
                f"Stretch plan adds +{delta:.1f} readiness vs baseline "
                f"({baseline.projected_readiness:.1f} → {stretch.projected_readiness:.1f})."
            )
        if forecast.top_drivers:
            lines.append(f"Focus interventions on: {', '.join(forecast.top_drivers)}.")
        return CopilotQueryResponse(
            intent=intent,
            answer="\n".join(lines),
            confidence="high",
            sources=[CopilotSourceResponse(label="Forecast scenarios", reference="GET /forecasting/scenarios")],
        )

    return map_student_forecast_to_copilot_response(intent="goal_attainment_probability", forecast=forecast)
