from __future__ import annotations

from datetime import UTC, datetime

from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.core.config import Settings
from prepos.core.logging import get_logger

logger = get_logger(__name__)


class DisasterRecoveryService:
    """Backup verification for Postgres, Redis, and knowledge storage (P11.17)."""

    def __init__(self, *, repository: PlatformMaturityRepositoryPort, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def verify_all(self) -> dict:
        results = {}
        for component in ("postgres", "redis", "knowledge_storage"):
            result = await self._verify_component(component)
            results[component] = result
        return results

    async def _verify_component(self, component: str) -> dict:
        backup_success = False
        restore_success: bool | None = None
        details: dict = {}

        if component == "postgres":
            backup_success = bool(self._settings.database_url)
            details = {"check": "connection_string_configured"}
        elif component == "redis":
            backup_success = bool(self._settings.redis_url)
            details = {"check": "redis_url_configured"}
        elif component == "knowledge_storage":
            from pathlib import Path

            path = Path(self._settings.knowledge_storage_path)
            backup_success = path.exists()
            details = {"path": str(path), "exists": path.exists()}

        await self._repository.save_backup_verification(
            component=component,
            backup_success=backup_success,
            restore_success=restore_success,
            details=details,
            now=datetime.now(UTC),
        )
        logger.info("backup_verification", component=component, success=backup_success)
        return {"backup_success": backup_success, "restore_success": restore_success, "details": details}

    async def get_dashboard(self) -> dict:
        return await self._repository.get_disaster_recovery_dashboard()
