from __future__ import annotations

from uuid import UUID

from prepos.application.institution_outcomes.ports import InstitutionOutcomeRepositoryPort


class InstitutionOutcomeAnalyticsService:
    def __init__(self, *, repository: InstitutionOutcomeRepositoryPort) -> None:
        self._repository = repository

    async def export_roi_csv(self, *, tenant_id: UUID) -> str:
        rows = await self._repository.export_roi_rows(tenant_id=tenant_id, limit=2000)
        lines = [
            "subject_key,initiative_type,title,roi_score,readiness_gain,forecast_gain,"
            "cohort_health_gain,risk_reduction,created_at"
        ]
        for row in rows:
            lines.append(
                f"{row.get('subject_key', '')},{row.get('initiative_type', '')},"
                f"\"{row.get('title', '')}\",{row.get('roi_score', '')},"
                f"{row.get('readiness_gain', '')},{row.get('forecast_gain', '')},"
                f"{row.get('cohort_health_gain', '')},{row.get('risk_reduction', '')},"
                f"{row.get('created_at', '')}"
            )
        return "\n".join(lines) + "\n"
