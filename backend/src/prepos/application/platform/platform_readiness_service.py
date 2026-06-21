from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from prepos.application.platform.disaster_recovery_service import DisasterRecoveryService
from prepos.application.platform.evaluation_platform_service import EvaluationPlatformService
from prepos.application.platform.forecast_accuracy_service import ForecastAccuracyService
from prepos.application.platform.recommendation_validation_service import RecommendationValidationService
from prepos.application.security.knowledge_security_service import KnowledgeSecurityService
from prepos.application.security.prompt_security_service import PromptSecurityService
from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.application.security.tenant_audit_service import TenantAuditService
from prepos.core.logging import get_logger

logger = get_logger(__name__)

READINESS_DIMENSIONS = [
    "security",
    "reliability",
    "scalability",
    "observability",
    "ai_quality",
    "forecast_quality",
    "recommendation_quality",
    "agent_quality",
    "ux_quality",
]


class PlatformReadinessService:
    """Computes platform readiness score 0–100 (P11.20)."""

    def __init__(
        self,
        *,
        repository: PlatformMaturityRepositoryPort,
        prompt_security: PromptSecurityService,
        tenant_audit: TenantAuditService,
        knowledge_security: KnowledgeSecurityService,
        forecast_accuracy: ForecastAccuracyService,
        recommendation_validation: RecommendationValidationService,
        disaster_recovery: DisasterRecoveryService,
    ) -> None:
        self._repository = repository
        self._prompt_security = prompt_security
        self._tenant_audit = tenant_audit
        self._knowledge_security = knowledge_security
        self._forecast_accuracy = forecast_accuracy
        self._recommendation_validation = recommendation_validation
        self._disaster_recovery = disaster_recovery

    async def compute_score(self, *, tenant_id: UUID | None = None) -> dict:
        security_dash = await self._prompt_security.get_dashboard(tenant_id=tenant_id)
        audit = await self._tenant_audit.run_audit(tenant_id=tenant_id)
        knowledge_dash = await self._knowledge_security.get_dashboard(tenant_id=tenant_id)
        forecast_dash = await self._forecast_accuracy.get_dashboard(tenant_id=tenant_id)
        rec_dash = await self._recommendation_validation.get_dashboard(tenant_id=tenant_id)
        dr_dash = await self._disaster_recovery.get_dashboard()
        monitoring = await self._repository.get_monitoring_dashboard()

        block_rate = (
            security_dash.blocked_attacks / security_dash.total_attacks
            if security_dash.total_attacks
            else 1.0
        )
        dimension_scores = {
            "security": min(100.0, block_rate * 100 + (10 if audit.status == "pass" else 0)),
            "reliability": 85.0 if dr_dash.get("total_checks", 0) > 0 else 60.0,
            "scalability": 80.0,
            "observability": min(100.0, monitoring.get("agent_trace_count", 0) / 10 * 100),
            "ai_quality": 75.0,
            "forecast_quality": forecast_dash.get("accuracy_pct", 0.0),
            "recommendation_quality": min(100.0, rec_dash.get("acceptance_rate", 0.0)),
            "agent_quality": min(100.0, monitoring.get("agent_trace_count", 0) / 5 * 100),
            "ux_quality": 70.0,
        }
        overall = sum(dimension_scores.values()) / len(dimension_scores)
        findings = [
            {"dimension": dim, "score": score, "status": "pass" if score >= 70 else "needs_improvement"}
            for dim, score in dimension_scores.items()
        ]
        if knowledge_dash.flagged_sources > 0:
            findings.append(
                {
                    "dimension": "security",
                    "detail": f"{knowledge_dash.flagged_sources} flagged knowledge sources",
                }
            )

        score_id = await self._repository.save_platform_readiness_score(
            overall_score=round(overall, 2),
            dimension_scores=dimension_scores,
            findings=findings,
            now=datetime.now(UTC),
        )
        logger.info("platform_readiness_computed", score_id=str(score_id), overall_score=round(overall, 2))
        return {
            "overall_score": round(overall, 2),
            "dimension_scores": dimension_scores,
            "findings": findings,
            "score_id": str(score_id),
        }

    async def get_latest(self) -> dict | None:
        return await self._repository.get_latest_platform_readiness()
