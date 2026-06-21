from __future__ import annotations

from prepos.application.security.ports import PlatformMaturityRepositoryPort


class MonitoringService:
    """Production monitoring dashboard aggregation (P11.16)."""

    def __init__(self, *, repository: PlatformMaturityRepositoryPort) -> None:
        self._repository = repository

    async def get_dashboard(self) -> dict:
        return await self._repository.get_monitoring_dashboard()


class OutcomeMeasurementService:
    """Institution-wide outcome KPIs (P11.19)."""

    def __init__(self, *, repository: PlatformMaturityRepositoryPort) -> None:
        self._repository = repository

    async def get_dashboard(self, *, tenant_id) -> dict:
        return await self._repository.get_outcome_dashboard(tenant_id=tenant_id)
