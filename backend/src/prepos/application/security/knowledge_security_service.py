from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from prepos.application.security.models import KnowledgeSecurityDashboardResponse
from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.application.security.prompt_injection_detector import detect_prompt_injection
from prepos.application.security.prompt_risk_scoring import score_prompt_risk
from prepos.core.logging import get_logger
from prepos.domain.knowledge.entities import KnowledgeSourceStatus

logger = get_logger(__name__)

QUARANTINE_THRESHOLD = 50.0
REVIEW_THRESHOLD = 25.0


class KnowledgeScanResult(BaseModel):
    risk_score: float
    risk_level: str
    attack_categories: list[str] = Field(default_factory=list)
    flagged: bool
    recommended_status: str | None = None
    scan_id: UUID | None = None


class KnowledgeSecurityService:
    def __init__(self, *, repository: PlatformMaturityRepositoryPort) -> None:
        self._repository = repository

    def scan_content(self, text: str) -> KnowledgeScanResult:
        detection = detect_prompt_injection(text)
        assessment = score_prompt_risk(detection)
        flagged = bool(detection.categories)
        recommended_status: str | None = None
        if assessment.risk_score >= QUARANTINE_THRESHOLD:
            recommended_status = KnowledgeSourceStatus.QUARANTINED.value
        elif assessment.risk_score >= REVIEW_THRESHOLD:
            recommended_status = KnowledgeSourceStatus.SECURITY_REVIEW_REQUIRED.value
        return KnowledgeScanResult(
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level.value,
            attack_categories=detection.categories,
            flagged=flagged,
            recommended_status=recommended_status,
        )

    async def scan_and_persist(
        self,
        *,
        tenant_id: UUID | None,
        source_id: UUID,
        text: str,
    ) -> KnowledgeScanResult:
        result = self.scan_content(text)
        scan_id = await self._repository.save_knowledge_security_scan(
            tenant_id=tenant_id,
            source_id=source_id,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            attack_categories=result.attack_categories,
            flagged=result.flagged,
            scan_status=result.recommended_status or "clean",
            details={"text_length": len(text)},
            now=datetime.now(UTC),
        )
        logger.info(
            "knowledge_security_scan",
            source_id=str(source_id),
            risk_score=result.risk_score,
            flagged=result.flagged,
            recommended_status=result.recommended_status,
        )
        return result.model_copy(update={"scan_id": scan_id})

    async def get_dashboard(self, *, tenant_id: UUID | None) -> KnowledgeSecurityDashboardResponse:
        return await self._repository.get_knowledge_security_dashboard(tenant_id=tenant_id)

    async def list_scans(
        self,
        *,
        tenant_id: UUID | None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        return await self._repository.list_knowledge_security_scans(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )
