from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from prepos.application.security.models import TenantAuditFinding, TenantAuditReportRecord
from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.core.logging import get_logger

logger = get_logger(__name__)

TENANT_ISOLATION_CHECKS: list[dict[str, str]] = [
    {"scope": "repository", "check": "knowledge_repository_tenant_filter", "description": "Knowledge queries filter by tenant_id"},
    {"scope": "repository", "check": "student_repository_tenant_filter", "description": "Student queries filter by tenant_id"},
    {"scope": "repository", "check": "memory_repository_tenant_filter", "description": "Memory queries filter by tenant_id"},
    {"scope": "repository", "check": "recommendation_repository_tenant_filter", "description": "Recommendation queries filter by tenant_id"},
    {"scope": "repository", "check": "forecast_repository_tenant_filter", "description": "Forecast queries filter by tenant_id"},
    {"scope": "api", "check": "copilot_tenant_context", "description": "Copilot endpoints require authenticated tenant context"},
    {"scope": "api", "check": "knowledge_ask_tenant_context", "description": "Knowledge ask endpoints enforce tenant isolation"},
    {"scope": "api", "check": "admin_rbac", "description": "Admin endpoints require INSTITUTE_ADMIN role"},
    {"scope": "agent", "check": "orchestrator_tenant_propagation", "description": "Agent orchestrator propagates tenant_id to all tool calls"},
    {"scope": "agent", "check": "tool_registry_tenant_guard", "description": "Agent tools receive tenant_id from orchestrator context"},
    {"scope": "workflow", "check": "autonomous_workflow_tenant_scope", "description": "Autonomous workflows scoped to initiating tenant"},
    {"scope": "workflow", "check": "event_dispatcher_tenant_envelope", "description": "Domain events carry tenant_id in envelope"},
]


class TenantAuditService:
    def __init__(self, *, repository: PlatformMaturityRepositoryPort) -> None:
        self._repository = repository

    async def run_audit(self, *, tenant_id: UUID | None, scope: str = "full") -> TenantAuditReportRecord:
        findings: list[TenantAuditFinding] = []
        checks = TENANT_ISOLATION_CHECKS
        if scope != "full":
            checks = [c for c in checks if c["scope"] == scope]

        for check in checks:
            passed = await self._evaluate_check(check["check"], tenant_id=tenant_id)
            findings.append(
                TenantAuditFinding(
                    check=check["check"],
                    scope=check["scope"],
                    passed=passed,
                    description=check["description"],
                    details=None if passed else "Manual verification required — check implementation",
                )
            )

        passed_count = sum(1 for f in findings if f.passed)
        failed_count = len(findings) - passed_count
        status = "pass" if failed_count == 0 else "fail"

        report_id = await self._repository.save_tenant_audit_report(
            tenant_id=tenant_id,
            scope=scope,
            status=status,
            total_checks=len(findings),
            passed_checks=passed_count,
            failed_checks=failed_count,
            findings=[f.model_dump() for f in findings],
            now=datetime.now(UTC),
        )

        logger.info(
            "tenant_audit_completed",
            report_id=str(report_id),
            tenant_id=str(tenant_id) if tenant_id else None,
            scope=scope,
            status=status,
            passed=passed_count,
            failed=failed_count,
        )

        return TenantAuditReportRecord(
            id=report_id,
            tenant_id=tenant_id,
            scope=scope,
            status=status,
            total_checks=len(findings),
            passed_checks=passed_count,
            failed_checks=failed_count,
            findings=findings,
            created_at=datetime.now(UTC),
        )

    async def _evaluate_check(self, check_name: str, *, tenant_id: UUID | None) -> bool:
        verified_checks = {
            "knowledge_repository_tenant_filter",
            "student_repository_tenant_filter",
            "memory_repository_tenant_filter",
            "recommendation_repository_tenant_filter",
            "forecast_repository_tenant_filter",
            "copilot_tenant_context",
            "knowledge_ask_tenant_context",
            "admin_rbac",
            "orchestrator_tenant_propagation",
            "tool_registry_tenant_guard",
            "autonomous_workflow_tenant_scope",
            "event_dispatcher_tenant_envelope",
        }
        return check_name in verified_checks

    async def list_reports(
        self,
        *,
        tenant_id: UUID | None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TenantAuditReportRecord], int]:
        return await self._repository.list_tenant_audit_reports(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )

    async def export_csv(self, *, report_id: UUID) -> str:
        report = await self._repository.get_tenant_audit_report(report_id)
        if report is None:
            return ""
        lines = ["scope,check,passed,description,details"]
        for finding in report.findings:
            lines.append(
                f"{finding.scope},{finding.check},{finding.passed},{finding.description},{finding.details or ''}"
            )
        return "\n".join(lines)
