from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from prepos.application.security.models import (
    PromptSecurityDashboardResponse,
    PromptSecurityEventRecord,
)
from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.application.security.prompt_injection_detector import detect_prompt_injection
from prepos.application.security.prompt_risk_scoring import score_prompt_risk
from prepos.application.security.prompt_sanitizer import redact_for_logging, sanitize_prompt
from prepos.core.exceptions import DomainError
from prepos.core.logging import get_logger

logger = get_logger(__name__)


class PromptSecurityResult(BaseModel):
    allowed: bool
    risk_score: float
    risk_level: str
    blocked_reason: str | None = None
    sanitized_prompt: str
    attack_categories: list[str] = Field(default_factory=list)
    event_id: UUID | None = None


class PromptInjectionBlockedError(DomainError):
    code = "PROMPT_INJECTION_BLOCKED"
    message = "Prompt blocked due to security policy."


class PromptSecurityService:
    def __init__(self, *, repository: PlatformMaturityRepositoryPort) -> None:
        self._repository = repository

    async def evaluate_prompt(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        source: str,
        prompt: str,
        trace_id: UUID | None = None,
        block_on_high: bool = True,
    ) -> PromptSecurityResult:
        sanitized = sanitize_prompt(prompt)
        detection = detect_prompt_injection(sanitized)
        assessment = score_prompt_risk(detection)
        blocked = assessment.blocked if block_on_high else False
        blocked_reason = assessment.blocked_reason if blocked else None

        event_id = await self._repository.save_prompt_security_event(
            tenant_id=tenant_id,
            user_id=user_id,
            source=source,
            prompt_text=redact_for_logging(sanitized),
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level.value,
            attack_categories=detection.categories,
            blocked=blocked,
            blocked_reason=blocked_reason,
            trace_id=trace_id,
            now=datetime.now(UTC),
        )

        logger.info(
            "prompt_security_evaluated",
            event_id=str(event_id),
            tenant_id=str(tenant_id),
            source=source,
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level.value,
            blocked=blocked,
            categories=detection.categories,
        )

        if blocked:
            raise PromptInjectionBlockedError(
                blocked_reason or "Prompt blocked due to security policy.",
                details={
                    "risk_score": assessment.risk_score,
                    "risk_level": assessment.risk_level.value,
                    "attack_categories": detection.categories,
                    "event_id": str(event_id),
                },
            )

        return PromptSecurityResult(
            allowed=True,
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level.value,
            blocked_reason=None,
            sanitized_prompt=sanitized,
            attack_categories=detection.categories,
            event_id=event_id,
        )

    async def get_dashboard(
        self,
        *,
        tenant_id: UUID | None,
        days: int = 30,
    ) -> PromptSecurityDashboardResponse:
        return await self._repository.get_prompt_security_dashboard(tenant_id=tenant_id, days=days)

    async def list_events(
        self,
        *,
        tenant_id: UUID | None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PromptSecurityEventRecord], int]:
        return await self._repository.list_prompt_security_events(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )
