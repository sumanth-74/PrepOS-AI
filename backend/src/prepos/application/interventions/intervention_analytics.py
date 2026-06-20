from __future__ import annotations

from uuid import UUID

from prepos.application.interventions.ports import InterventionRepositoryPort


class InterventionAnalyticsService:
    def __init__(self, *, repository: InterventionRepositoryPort) -> None:
        self._repository = repository

    async def get_admin_dashboard(self, *, tenant_id: UUID) -> dict[str, object]:
        return await self._repository.get_admin_metrics(tenant_id=tenant_id)

    async def export_csv(self, *, tenant_id: UUID) -> str:
        rows = await self._repository.export_rows(tenant_id=tenant_id, limit=1000)
        lines = [
            "intervention_id,student_id,intervention_type,concept_id,predicted_gain,actual_gain,effectiveness,status,created_at"
        ]
        for row in rows:
            lines.append(
                f"{row['intervention_id']},{row['student_id']},{row['intervention_type']},"
                f"{row.get('concept_id') or ''},{row['predicted_gain']},{row.get('actual_gain') or ''},"
                f"{row.get('effectiveness_score') or ''},{row['status']},{row['created_at']}"
            )
        return "\n".join(lines) + "\n"
