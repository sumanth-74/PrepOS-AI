from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

import structlog

from prepos.application.forecasting.forecast_analytics import ForecastAnalyticsService
from prepos.application.forecasting.forecast_explainer import explain_forecast
from prepos.application.forecasting.forecast_models import (
    CustomScenarioRequest,
    ForecastAdminResponse,
    ForecastExplainResponse,
    ForecastHistoryEntry,
    ForecastHistoryResponse,
    ForecastScenarioResponse,
    GoalForecastResponse,
)
from prepos.application.forecasting.goal_forecasting_engine import ForecastEngineInputs, run_goal_forecast
from prepos.application.forecasting.ports import ForecastingRepositoryPort
from prepos.application.forecasting.scenario_simulator import ScenarioResult, simulate_custom_scenario, simulate_default_scenarios
from prepos.application.goal.ports import GoalRepositoryPort
from prepos.application.memory.memory_service import CoachingMemoryService
from prepos.application.planning.planning_service import AdaptivePlanningService
from prepos.application.recommendations.recommendation_engine import format_concept_name
from prepos.application.recommendations.recommendation_service import LearningRecommendationService
from prepos.application.twin.twin_read_service import TwinReadService
from prepos.domain.scoring.readiness_forecast_v1 import compute_days_remaining

logger = structlog.get_logger(__name__)


class GoalForecastingService:
    def __init__(
        self,
        *,
        repository: ForecastingRepositoryPort,
        goal_repository: GoalRepositoryPort,
        twin_read_service: TwinReadService,
        planning_service: AdaptivePlanningService,
        recommendation_service: LearningRecommendationService,
        memory_service: CoachingMemoryService,
        analytics_service: ForecastAnalyticsService | None = None,
    ) -> None:
        self._repository = repository
        self._goal_repository = goal_repository
        self._twin_read_service = twin_read_service
        self._planning_service = planning_service
        self._recommendation_service = recommendation_service
        self._memory_service = memory_service
        self._analytics = analytics_service or ForecastAnalyticsService(repository=repository)

    async def generate_forecast(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> GoalForecastResponse:
        resolved_exam = exam_id or "upsc_cse"
        now = datetime.now(UTC)
        inputs, top_drivers, goal_id, target_date = await self._build_inputs(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            exam_id=resolved_exam,
        )
        result = run_goal_forecast(inputs)
        explanations = explain_forecast(
            result=result,
            target_readiness=inputs.target_readiness,
            top_drivers=top_drivers,
            adherence_rate=inputs.adherence_rate,
            effectiveness_multiplier=inputs.effectiveness_multiplier,
        )
        scenarios = simulate_default_scenarios(
            base_weekly_minutes=int(inputs.weekly_minutes),
            engine_inputs=inputs,
        )
        await self._persist_forecast(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            goal_id=goal_id,
            exam_id=resolved_exam,
            target_date=target_date,
            inputs=inputs,
            result=result,
            top_drivers=top_drivers,
            scenarios=scenarios,
            explanations=explanations,
            now=now,
        )
        logger.info(
            "forecast_generated",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            goal_id=str(goal_id),
            probability=result.probability_of_success,
            projected_readiness=result.projected_readiness,
            target_readiness=inputs.target_readiness,
        )
        stored = await self.get_current_forecast(
            tenant_id=tenant_id,
            user_id=user_id,
            exam_id=resolved_exam,
        )
        assert stored is not None
        return stored

    async def get_current_forecast(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
    ) -> GoalForecastResponse | None:
        row = await self._repository.get_current_forecast(
            tenant_id=tenant_id,
            user_id=user_id,
            exam_id=exam_id or "upsc_cse",
        )
        if row is None:
            return None
        forecast = row["forecast"]
        scenarios = row["scenarios"]
        await self._repository.record_event(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=forecast.student_id,
            forecast_id=forecast.id,
            scenario_id=None,
            event_type="scenario_viewed",
            metadata_json={},
            created_at=datetime.now(UTC),
        )
        return GoalForecastResponse(
            forecast_id=forecast.id,
            exam_id=forecast.exam_id,
            forecast_date=forecast.forecast_date,
            target_date=forecast.target_date,
            current_readiness=float(forecast.current_readiness),
            projected_readiness=float(forecast.projected_readiness),
            target_readiness=float(forecast.target_readiness),
            probability_of_success=float(forecast.probability_of_success),
            forecast_status=forecast.forecast_status,
            top_drivers=list(forecast.top_drivers_json),
            scenarios=[
                ForecastScenarioResponse(
                    id=scenario.id,
                    scenario_type=scenario.scenario_type,
                    scenario_name=scenario.scenario_name,
                    weekly_minutes=scenario.weekly_minutes,
                    projected_readiness=float(scenario.projected_readiness),
                    projected_score=float(scenario.projected_score) if scenario.projected_score else None,
                    probability_of_success=float(scenario.probability_of_success),
                )
                for scenario in scenarios
            ],
            explanations=list(forecast.metadata_json.get("explanations", [])),
            generated_at=forecast.created_at,
        )

    async def get_scenarios(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
    ) -> list[ForecastScenarioResponse]:
        current = await self.get_current_forecast(
            tenant_id=tenant_id,
            user_id=user_id,
            exam_id=exam_id,
        )
        return current.scenarios if current else []

    async def simulate_custom_scenario(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        request: CustomScenarioRequest,
    ) -> ForecastScenarioResponse:
        inputs, _, _goal_id, _target_date = await self._build_inputs(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            exam_id=request.exam_id,
        )
        scenario = simulate_custom_scenario(weekly_minutes=request.weekly_minutes, engine_inputs=inputs)
        current = await self._repository.get_current_forecast(
            tenant_id=tenant_id,
            user_id=user_id,
            exam_id=request.exam_id,
        )
        forecast_id = current["forecast"].id if current else None
        scenario_id = None
        if forecast_id is not None:
            ids = await self._repository.create_scenarios(
                forecast_id=forecast_id,
                scenarios=[_scenario_payload(scenario)],
                now=datetime.now(UTC),
            )
            scenario_id = ids[0]
        await self._repository.record_event(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            forecast_id=forecast_id,
            scenario_id=scenario_id,
            event_type="scenario_created",
            metadata_json={"weekly_minutes": request.weekly_minutes},
            created_at=datetime.now(UTC),
        )
        logger.info(
            "scenario_simulated",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            goal_id=None,
            probability=scenario.probability_of_success,
            projected_readiness=scenario.projected_readiness,
            target_readiness=inputs.target_readiness,
        )
        return ForecastScenarioResponse(
            id=scenario_id or UUID(int=0),
            scenario_type=scenario.scenario_type,
            scenario_name=scenario.scenario_name,
            weekly_minutes=scenario.weekly_minutes,
            projected_readiness=scenario.projected_readiness,
            projected_score=scenario.projected_score,
            probability_of_success=scenario.probability_of_success,
        )

    async def explain_forecast(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> ForecastExplainResponse:
        inputs, top_drivers, _goal_id, _target_date = await self._build_inputs(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            exam_id=exam_id or "upsc_cse",
        )
        result = run_goal_forecast(inputs)
        explanations = explain_forecast(
            result=result,
            target_readiness=inputs.target_readiness,
            top_drivers=top_drivers,
            adherence_rate=inputs.adherence_rate,
            effectiveness_multiplier=inputs.effectiveness_multiplier,
        )
        return ForecastExplainResponse(
            current_readiness=inputs.current_readiness,
            projected_readiness=result.projected_readiness,
            target_readiness=inputs.target_readiness,
            probability_of_success=result.probability_of_success,
            forecast_status=result.forecast_status,
            top_drivers=top_drivers,
            explanations=explanations,
            weekly_gain=result.weekly_gain,
            adherence_rate=inputs.adherence_rate,
            effectiveness_multiplier=inputs.effectiveness_multiplier,
        )

    async def get_history(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
        limit: int = 20,
    ) -> ForecastHistoryResponse:
        rows = await self._repository.list_forecast_history(
            tenant_id=tenant_id,
            user_id=user_id,
            exam_id=exam_id or "upsc_cse",
            limit=limit,
        )
        forecasts = [
            ForecastHistoryEntry(
                forecast_id=row["forecast"].id,
                forecast_date=row["forecast"].forecast_date,
                projected_readiness=float(row["forecast"].projected_readiness),
                probability_of_success=float(row["forecast"].probability_of_success),
                forecast_status=row["forecast"].forecast_status,
                created_at=row["forecast"].created_at,
            )
            for row in rows
        ]
        return ForecastHistoryResponse(forecasts=forecasts, total=len(forecasts))

    async def get_admin_dashboard(self, *, tenant_id: UUID) -> ForecastAdminResponse:
        metrics = await self._analytics.get_admin_dashboard(tenant_id=tenant_id)
        return ForecastAdminResponse(
            total_forecasts=int(metrics["total_forecasts"]),
            forecasts_last_30_days=int(metrics["forecasts_last_30_days"]),
            average_probability=float(metrics["average_probability"]),
            on_track_rate=float(metrics["on_track_rate"]),
            average_projected_gain=float(metrics["average_projected_gain"]),
            scenario_usage=list(metrics["scenario_usage"]),
            event_counts=list(metrics["event_counts"]),
        )

    async def export_csv(self, *, tenant_id: UUID) -> str:
        return await self._analytics.export_csv(tenant_id=tenant_id)

    async def _build_inputs(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> tuple[ForecastEngineInputs, list[str], UUID, date]:
        goal = await self._goal_repository.get_goal(tenant_id, student_id, exam_id)
        if goal is None:
            raise ValueError("Goal not found. Create a goal before generating a forecast.")

        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        current_readiness = float(dashboard.readiness_score or 0)
        target_readiness = float(goal.target_readiness_score)
        now = datetime.now(UTC)
        weeks_remaining = max(1, compute_days_remaining(target_date=goal.target_date, current_time=now) // 7)

        plan = await self._planning_service.get_current_plan(
            tenant_id=tenant_id,
            user_id=user_id,
            exam_id=exam_id,
        )
        if plan is not None:
            all_items = plan.today_items + plan.week_items + plan.next_week_draft
            completed = sum(1 for item in all_items if item.completion_status == "completed")
            adherence_rate = completed / len(all_items) if all_items else float(dashboard.completion_rate or 0.5)
            weekly_minutes = plan.daily_minutes_budget * 7
        else:
            adherence_rate = float(dashboard.completion_rate or 0.5)
            weekly_minutes = goal.daily_capacity_minutes * 7

        memory = await self._memory_service.load_student_context(tenant_id=tenant_id, user_id=user_id)
        effectiveness_values = [
            float(item.memory_value.get("effectiveness_score", 0))
            for item in memory.outcome_summaries
        ]
        effectiveness_multiplier = (
            sum(effectiveness_values) / len(effectiveness_values) if effectiveness_values else 1.0
        )
        if dashboard.historical_effectiveness is not None:
            effectiveness_multiplier = max(
                effectiveness_multiplier,
                float(dashboard.historical_effectiveness),
            )

        twin_stability = 1.0
        if dashboard.projected_readiness is not None:
            delta = abs(float(dashboard.projected_readiness) - current_readiness)
            twin_stability = max(0.4, 1.0 - (delta / 100.0))

        recommendations = await self._recommendation_service.get_student_recommendations(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            user_id=user_id,
            limit=3,
        )
        top_drivers = [item.concept_name for item in recommendations.recommendations[:3]]
        if not top_drivers and dashboard.top_positive_drivers:
            top_drivers = [format_concept_name(item) for item in dashboard.top_positive_drivers[:3]]

        inputs = ForecastEngineInputs(
            current_readiness=current_readiness,
            target_readiness=target_readiness,
            weekly_minutes=float(weekly_minutes),
            adherence_rate=min(1.0, max(0.0, adherence_rate)),
            effectiveness_multiplier=min(3.0, max(0.5, effectiveness_multiplier)),
            forecast_stability=twin_stability,
            weeks_remaining=weeks_remaining,
        )
        return inputs, top_drivers, goal.id, goal.target_date

    async def _persist_forecast(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        goal_id: UUID,
        exam_id: str,
        target_date: date,
        inputs: ForecastEngineInputs,
        result: object,
        top_drivers: list[str],
        scenarios: list[ScenarioResult],
        explanations: list[str],
        now: datetime,
    ) -> UUID:
        from prepos.application.forecasting.goal_forecasting_engine import ForecastEngineResult

        assert isinstance(result, ForecastEngineResult)
        forecast_id = await self._repository.create_forecast(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            goal_id=goal_id,
            exam_id=exam_id,
            forecast_date=now.date(),
            target_date=target_date,
            current_readiness=inputs.current_readiness,
            projected_readiness=result.projected_readiness,
            target_readiness=inputs.target_readiness,
            probability_of_success=result.probability_of_success,
            forecast_status=result.forecast_status,
            top_drivers=top_drivers,
            metadata_json={
                "explanations": explanations,
                "weekly_gain": result.weekly_gain,
            },
            now=now,
        )
        await self._repository.create_scenarios(
            forecast_id=forecast_id,
            scenarios=[_scenario_payload(item) for item in scenarios],
            now=now,
        )
        await self._repository.record_event(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            forecast_id=forecast_id,
            scenario_id=None,
            event_type="forecast_generated",
            metadata_json={"status": result.forecast_status},
            created_at=now,
        )
        return forecast_id


def _scenario_payload(scenario: ScenarioResult) -> dict[str, object]:
    return {
        "scenario_type": scenario.scenario_type,
        "scenario_name": scenario.scenario_name,
        "weekly_minutes": scenario.weekly_minutes,
        "projected_readiness": scenario.projected_readiness,
        "projected_score": scenario.projected_score,
        "probability_of_success": scenario.probability_of_success,
    }
