from __future__ import annotations

from uuid import UUID

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse
from prepos.application.forecasting.forecast_models import GoalForecastResponse
from prepos.application.forecasting.forecast_service import GoalForecastingService

STUDENT_FORECASTING_INTENTS: frozenset[str] = frozenset(
    {
        "goal_forecast",
        "target_probability",
        "what_if_scenario",
        "readiness_projection",
        "goal_gap",
        "best_improvement_path",
    }
)

STUDENT_FORECASTING_INTROS: dict[str, str] = {
    "goal_forecast": "Your goal forecast:",
    "target_probability": "Probability of reaching your target:",
    "what_if_scenario": "What-if scenario comparison:",
    "readiness_projection": "Readiness projection:",
    "goal_gap": "Gap to your goal:",
    "best_improvement_path": "Best improvement path from forecast drivers:",
}


def map_student_forecast_to_copilot_response(
    *,
    intent: str,
    forecast: GoalForecastResponse,
) -> CopilotQueryResponse:
    intro = STUDENT_FORECASTING_INTROS.get(intent, "Goal forecast:")
    lines = [
        intro,
        "",
        f"Current readiness: {forecast.current_readiness:.1f}",
        f"Projected readiness: {forecast.projected_readiness:.1f}",
        f"Target readiness: {forecast.target_readiness:.1f}",
        f"Probability of success: {forecast.probability_of_success:.0f}%",
        f"Status: {forecast.forecast_status.replace('_', ' ')}",
    ]
    if intent == "goal_gap":
        gap = max(0.0, forecast.target_readiness - forecast.projected_readiness)
        lines.append(f"Remaining gap: {gap:.1f} readiness points.")
    if intent in {"what_if_scenario", "goal_forecast"} and forecast.scenarios:
        lines.append("")
        lines.append("Scenarios:")
        for scenario in forecast.scenarios[:5]:
            hours = scenario.weekly_minutes / 60
            lines.append(
                f"- {scenario.scenario_name}: {hours:.1f}h/week → "
                f"{scenario.projected_readiness:.1f} readiness "
                f"({scenario.probability_of_success:.0f}% success)"
            )
    if intent == "best_improvement_path" and forecast.top_drivers:
        lines.append("")
        lines.append(f"Top drivers: {', '.join(forecast.top_drivers)}")
    if forecast.explanations:
        lines.extend(["", *forecast.explanations[:3]])

    return CopilotQueryResponse(
        intent=intent,
        answer="\n".join(lines),
        confidence="high",
        sources=[
            CopilotSourceResponse(label="Goal forecast", reference="GET /forecasting/current"),
            CopilotSourceResponse(label="Forecast scenarios", reference="GET /forecasting/scenarios"),
        ],
    )


async def build_student_forecast_response(
    *,
    intent: str,
    forecast_service: GoalForecastingService,
    tenant_id: UUID,
    user_id: UUID,
    student_id: UUID,
    exam_id: str | None,
) -> CopilotQueryResponse:
    resolved_exam = exam_id or "upsc_cse"
    forecast = await forecast_service.get_current_forecast(
        tenant_id=tenant_id,
        user_id=user_id,
        exam_id=resolved_exam,
    )
    if forecast is None:
        forecast = await forecast_service.generate_forecast(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            exam_id=resolved_exam,
        )
    return map_student_forecast_to_copilot_response(intent=intent, forecast=forecast)
