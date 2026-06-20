from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.forecasting.ports import ForecastingRepositoryPort
from prepos.infrastructure.db.models.goal_forecasting import (
    ForecastEventModel,
    ForecastScenarioModel,
    GoalForecastModel,
)


class SqlAlchemyForecastingRepository(ForecastingRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_forecast(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        goal_id: UUID,
        exam_id: str,
        forecast_date: date,
        target_date: date,
        current_readiness: float,
        projected_readiness: float,
        target_readiness: float,
        probability_of_success: float,
        forecast_status: str,
        top_drivers: list[str],
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID:
        forecast_id = uuid4()
        self._session.add(
            GoalForecastModel(
                id=forecast_id,
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                goal_id=goal_id,
                exam_id=exam_id,
                forecast_date=forecast_date,
                target_date=target_date,
                current_readiness=current_readiness,
                projected_readiness=projected_readiness,
                target_readiness=target_readiness,
                probability_of_success=probability_of_success,
                forecast_status=forecast_status,
                top_drivers_json=top_drivers,
                metadata_json=metadata_json,
                created_at=now,
            )
        )
        await self._session.flush()
        return forecast_id

    async def create_scenarios(
        self,
        *,
        forecast_id: UUID,
        scenarios: list[dict[str, object]],
        now: datetime,
    ) -> list[UUID]:
        ids: list[UUID] = []
        for scenario in scenarios:
            scenario_id = uuid4()
            ids.append(scenario_id)
            self._session.add(
                ForecastScenarioModel(
                    id=scenario_id,
                    forecast_id=forecast_id,
                    scenario_type=str(scenario["scenario_type"]),
                    scenario_name=str(scenario["scenario_name"]),
                    weekly_minutes=int(scenario["weekly_minutes"]),
                    projected_readiness=scenario["projected_readiness"],  # type: ignore[arg-type]
                    projected_score=scenario.get("projected_score"),  # type: ignore[arg-type]
                    probability_of_success=scenario["probability_of_success"],  # type: ignore[arg-type]
                    created_at=now,
                )
            )
        await self._session.flush()
        return ids

    async def get_current_forecast(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
    ) -> dict[str, object] | None:
        stmt = (
            select(GoalForecastModel)
            .where(
                GoalForecastModel.tenant_id == tenant_id,
                GoalForecastModel.user_id == user_id,
                GoalForecastModel.exam_id == exam_id,
            )
            .order_by(GoalForecastModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        forecast = result.scalar_one_or_none()
        if forecast is None:
            return None
        scenarios_stmt = select(ForecastScenarioModel).where(
            ForecastScenarioModel.forecast_id == forecast.id
        ).order_by(ForecastScenarioModel.weekly_minutes.asc())
        scenarios_result = await self._session.execute(scenarios_stmt)
        return {"forecast": forecast, "scenarios": list(scenarios_result.scalars())}

    async def list_scenarios(self, *, forecast_id: UUID) -> list[dict[str, object]]:
        stmt = select(ForecastScenarioModel).where(
            ForecastScenarioModel.forecast_id == forecast_id
        ).order_by(ForecastScenarioModel.weekly_minutes.asc())
        result = await self._session.execute(stmt)
        return [{"scenario": row} for row in result.scalars()]

    async def list_forecast_history(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = (
            select(GoalForecastModel)
            .where(
                GoalForecastModel.tenant_id == tenant_id,
                GoalForecastModel.user_id == user_id,
                GoalForecastModel.exam_id == exam_id,
            )
            .order_by(GoalForecastModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [{"forecast": row} for row in result.scalars()]

    async def record_event(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID | None,
        forecast_id: UUID | None,
        scenario_id: UUID | None,
        event_type: str,
        metadata_json: dict[str, object],
        created_at: datetime,
    ) -> UUID:
        event_id = uuid4()
        self._session.add(
            ForecastEventModel(
                id=event_id,
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                forecast_id=forecast_id,
                scenario_id=scenario_id,
                event_type=event_type,
                metadata_json=metadata_json,
                created_at=created_at,
            )
        )
        await self._session.flush()
        return event_id

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        total_stmt = select(func.count()).select_from(GoalForecastModel).where(
            GoalForecastModel.tenant_id == tenant_id
        )
        recent_stmt = select(func.count()).select_from(GoalForecastModel).where(
            GoalForecastModel.tenant_id == tenant_id,
            GoalForecastModel.created_at >= datetime.now(UTC) - timedelta(days=30),
        )
        avg_prob_stmt = select(func.avg(GoalForecastModel.probability_of_success)).where(
            GoalForecastModel.tenant_id == tenant_id
        )
        on_track_stmt = select(func.count()).select_from(GoalForecastModel).where(
            GoalForecastModel.tenant_id == tenant_id,
            GoalForecastModel.forecast_status == "on_track",
        )
        avg_gain_stmt = select(
            func.avg(GoalForecastModel.projected_readiness - GoalForecastModel.current_readiness)
        ).where(GoalForecastModel.tenant_id == tenant_id)

        total = int((await self._session.execute(total_stmt)).scalar_one())
        recent = int((await self._session.execute(recent_stmt)).scalar_one())
        avg_prob = float((await self._session.execute(avg_prob_stmt)).scalar_one() or 0)
        on_track = int((await self._session.execute(on_track_stmt)).scalar_one())
        avg_gain = float((await self._session.execute(avg_gain_stmt)).scalar_one() or 0)

        scenario_stmt = (
            select(ForecastScenarioModel.scenario_type, func.count())
            .join(GoalForecastModel, ForecastScenarioModel.forecast_id == GoalForecastModel.id)
            .where(GoalForecastModel.tenant_id == tenant_id)
            .group_by(ForecastScenarioModel.scenario_type)
        )
        scenario_rows = (await self._session.execute(scenario_stmt)).all()

        event_stmt = (
            select(ForecastEventModel.event_type, func.count())
            .where(ForecastEventModel.tenant_id == tenant_id)
            .group_by(ForecastEventModel.event_type)
        )
        event_rows = (await self._session.execute(event_stmt)).all()

        on_track_rate = round(on_track / total, 4) if total else 0.0
        return {
            "total_forecasts": total,
            "forecasts_last_30_days": recent,
            "average_probability": round(avg_prob, 2),
            "on_track_rate": on_track_rate,
            "average_projected_gain": round(avg_gain, 2),
            "scenario_usage": [{"scenario_type": t, "count": c} for t, c in scenario_rows],
            "event_counts": [{"event_type": t, "count": c} for t, c in event_rows],
        }

    async def export_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]:
        stmt = (
            select(GoalForecastModel)
            .where(GoalForecastModel.tenant_id == tenant_id)
            .order_by(GoalForecastModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows: list[dict[str, object]] = []
        for forecast in result.scalars():
            rows.append(
                {
                    "forecast_id": forecast.id,
                    "exam_id": forecast.exam_id,
                    "current_readiness": float(forecast.current_readiness),
                    "projected_readiness": float(forecast.projected_readiness),
                    "probability_of_success": float(forecast.probability_of_success),
                    "forecast_status": forecast.forecast_status,
                    "created_at": forecast.created_at.isoformat(),
                }
            )
        return rows
