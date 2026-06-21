from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.core.logging import get_logger

logger = get_logger(__name__)


class JobReliabilityService:
    """Background job reliability tracking (P11.6)."""

    def __init__(self, *, repository: PlatformMaturityRepositoryPort) -> None:
        self._repository = repository

    async def record_task_event(
        self,
        *,
        task_name: str,
        task_id: str,
        status: str,
        retry_count: int = 0,
        tenant_id: UUID | None = None,
        idempotency_key: str | None = None,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> UUID:
        event_id = await self._repository.save_background_job_event(
            tenant_id=tenant_id,
            task_name=task_name,
            task_id=task_id,
            status=status,
            retry_count=retry_count,
            idempotency_key=idempotency_key,
            error_message=error_message,
            metadata=metadata or {},
            now=datetime.now(UTC),
        )
        logger.info(
            "background_job_event",
            task_name=task_name,
            task_id=task_id,
            status=status,
            retry_count=retry_count,
        )
        return event_id

    async def get_dashboard(self) -> dict:
        return await self._repository.get_job_dashboard()
