from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from prepos.application.forecasting.ports import ForecastingRepositoryPort


class ForecastAnalyticsService:
    def __init__(self, *, repository: ForecastingRepositoryPort) -> None:
        self._repository = repository

    async def get_admin_dashboard(self, *, tenant_id: UUID) -> dict[str, object]:
        return await self._repository.get_admin_metrics(tenant_id=tenant_id)

    async def export_csv(self, *, tenant_id: UUID) -> str:
        rows = await self._repository.export_rows(tenant_id=tenant_id, limit=1000)
        lines = [
            "forecast_id,exam_id,current_readiness,projected_readiness,probability,status,created_at"
        ]
        for row in rows:
            lines.append(
                f"{row['forecast_id']},{row['exam_id']},{row['current_readiness']},"
                f"{row['projected_readiness']},{row['probability_of_success']},"
                f"{row['forecast_status']},{row['created_at']}"
            )
        return "\n".join(lines) + "\n"

    @staticmethod
    def forecast_accuracy(*, projected: float, actual: float) -> float:
        error = abs(projected - actual)
        return round(max(0.0, 100.0 - error), 2)

    @staticmethod
    def window_start(days: int = 30) -> datetime:
        return datetime.now(UTC) - timedelta(days=days)
