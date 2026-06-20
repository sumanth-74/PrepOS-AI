from __future__ import annotations

from uuid import UUID

from prepos.application.institution.ports import InstitutionRepositoryPort


class InstitutionAnalyticsService:
    def __init__(self, *, repository: InstitutionRepositoryPort) -> None:
        self._repository = repository

    async def get_admin_dashboard(self, *, tenant_id: UUID) -> dict[str, object]:
        return await self._repository.get_admin_metrics(tenant_id=tenant_id)

    async def export_csv(self, *, tenant_id: UUID) -> str:
        rows = await self._repository.export_rows(tenant_id=tenant_id, limit=2000)
        lines = [
            "insight_type,insight_key,title,severity,created_at,"
            "recommendation_type,priority_score,expected_impact"
        ]
        for row in rows:
            lines.append(
                f"{row.get('insight_type', '')},{row.get('insight_key', '')},"
                f"\"{row.get('title', '')}\",{row.get('severity', '')},"
                f"{row.get('created_at', '')},{row.get('recommendation_type', '')},"
                f"{row.get('priority_score', '')},{row.get('expected_impact', '')}"
            )
        return "\n".join(lines) + "\n"

    async def record_dashboard_viewed(self, *, tenant_id: UUID) -> None:
        from datetime import UTC, datetime

        await self._repository.record_event(
            tenant_id=tenant_id,
            event_type="institution_dashboard_viewed",
            metadata_json={},
            now=datetime.now(UTC),
        )
