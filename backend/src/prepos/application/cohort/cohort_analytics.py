from __future__ import annotations

from uuid import UUID

from prepos.application.cohort.ports import CohortRepositoryPort


class CohortAnalyticsService:
    def __init__(self, *, repository: CohortRepositoryPort) -> None:
        self._repository = repository

    async def get_admin_dashboard(self, *, tenant_id: UUID) -> dict[str, object]:
        return await self._repository.get_admin_metrics(tenant_id=tenant_id)

    async def export_csv(self, *, tenant_id: UUID) -> str:
        rows = await self._repository.export_rows(tenant_id=tenant_id, limit=2000)
        lines = [
            "cohort_id,snapshot_date,student_count,avg_readiness,avg_forecast,risk_count,created_at"
        ]
        for row in rows:
            lines.append(
                f"{row['cohort_id']},{row['snapshot_date']},{row['student_count']},"
                f"{row['avg_readiness']},{row['avg_forecast']},{row['risk_count']},{row['created_at']}"
            )
        return "\n".join(lines) + "\n"
