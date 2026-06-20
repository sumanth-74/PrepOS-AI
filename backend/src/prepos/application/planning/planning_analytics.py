from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from prepos.application.planning.ports import PlanningRepositoryPort


class PlanningAnalyticsService:
    def __init__(self, *, repository: PlanningRepositoryPort) -> None:
        self._repository = repository

    async def get_admin_dashboard(self, *, tenant_id: UUID) -> dict[str, object]:
        return await self._repository.get_admin_metrics(tenant_id=tenant_id)

    async def export_csv(self, *, tenant_id: UUID) -> str:
        rows = await self._repository.export_rows(tenant_id=tenant_id, limit=1000)
        lines = ["plan_id,concept_id,priority_score,scheduled_date,completion_status,event_type"]
        for row in rows:
            lines.append(
                f"{row.get('plan_id')},{row.get('concept_id')},{row.get('priority_score')},"
                f"{row.get('scheduled_date')},{row.get('completion_status')},{row.get('event_type')}"
            )
        return "\n".join(lines) + "\n"

    @staticmethod
    def completion_rate(*, completed: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return round(completed / total, 4)

    @staticmethod
    def adherence_rate(*, completed_on_schedule: int, due_items: int) -> float:
        if due_items <= 0:
            return 0.0
        return round(completed_on_schedule / due_items, 4)

    @staticmethod
    def window_start(days: int = 30) -> datetime:
        return datetime.now(UTC) - timedelta(days=days)
