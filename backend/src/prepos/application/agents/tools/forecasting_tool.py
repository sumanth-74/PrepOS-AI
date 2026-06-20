from __future__ import annotations

from prepos.application.agents.models import AgentContext, AgentResult
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.forecasting.forecast_service import GoalForecastingService


class ForecastingTool(BaseTool):
    name = "forecasting"

    def __init__(self, *, service: GoalForecastingService) -> None:
        self._service = service

    async def execute(self, *, context: AgentContext) -> AgentResult:
        if context.student_id is None:
            if context.persona == "admin":
                dashboard = await self._service.get_admin_dashboard(tenant_id=context.tenant_id)
                return self._success(
                    data=dashboard.model_dump(mode="json"),
                    reasoning="Loaded institution forecast dashboard.",
                    label="Forecasting",
                    reference="GET /admin/forecasting",
                )
            return self._failure(reasoning="student_id required for forecast tool.", tool_name=self.name)
        exam_id = context.exam_id or "upsc_cse"
        user_id = context.student_user_id or context.user_id
        forecast = await self._service.get_current_forecast(
            tenant_id=context.tenant_id,
            user_id=user_id,
            exam_id=exam_id,
        )
        if forecast is None:
            return self._failure(reasoning="No forecast available for student.", tool_name=self.name)
        return self._success(
            data=forecast.model_dump(mode="json"),
            reasoning=f"Current forecast loaded for exam {exam_id}.",
            label="Forecasting",
            reference="GET /forecasting/current",
        )
