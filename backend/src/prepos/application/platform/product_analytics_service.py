from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.core.logging import get_logger
from prepos.infrastructure.db.models.copilot_analytics import CopilotQueryModel
from prepos.infrastructure.db.models.foundation import UserModel

logger = get_logger(__name__)


class ProductAnalyticsService:
    """Product adoption and funnel analytics (P11.18)."""

    def __init__(
        self,
        *,
        repository: PlatformMaturityRepositoryPort,
        session: AsyncSession,
    ) -> None:
        self._repository = repository
        self._session = session

    async def compute_snapshot(self, *, tenant_id: UUID | None = None) -> dict:
        user_stmt = select(func.count(UserModel.id))
        query_stmt = select(func.count(CopilotQueryModel.id))
        if tenant_id is not None:
            user_stmt = user_stmt.where(UserModel.tenant_id == tenant_id)
            query_stmt = query_stmt.where(CopilotQueryModel.tenant_id == tenant_id)

        total_users = int(await self._session.scalar(user_stmt) or 0)
        total_queries = int(await self._session.scalar(query_stmt) or 0)
        metrics = {
            "weekly_active_users": total_users,
            "monthly_active_users": total_users,
            "copilot_adoption_pct": round(min(100.0, total_queries / max(total_users, 1) * 10), 2),
            "agent_mode_adoption_pct": 0.0,
            "funnels": {
                "signup": total_users,
                "active": total_users,
                "copilot": total_queries,
                "recommendations": 0,
                "planning": 0,
                "forecasting": 0,
            },
        }
        await self._repository.save_product_analytics_snapshot(
            tenant_id=tenant_id,
            snapshot_date=date.today(),
            metrics=metrics,
            now=datetime.now(UTC),
        )
        logger.info("product_analytics_snapshot", tenant_id=str(tenant_id) if tenant_id else None)
        return metrics

    async def get_dashboard(self, *, tenant_id: UUID | None = None) -> dict:
        cached = await self._repository.get_adoption_dashboard(tenant_id=tenant_id)
        if cached.get("weekly_active_users", 0) == 0:
            return await self.compute_snapshot(tenant_id=tenant_id)
        return cached
