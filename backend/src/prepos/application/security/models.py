from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PromptSecurityDashboardResponse(BaseModel):
    total_attacks: int
    blocked_attacks: int
    attack_categories: dict[str, int]
    tenant_distribution: dict[str, int]


class PromptSecurityEventRecord(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID | None
    source: str
    risk_score: float
    risk_level: str
    attack_categories: list[str]
    blocked: bool
    blocked_reason: str | None
    created_at: datetime


class KnowledgeSecurityDashboardResponse(BaseModel):
    total_scans: int
    flagged_sources: int
    quarantined_sources: int
    attack_categories: dict[str, int]


class TenantAuditFinding(BaseModel):
    check: str
    scope: str
    passed: bool
    description: str
    details: str | None = None


class TenantAuditReportRecord(BaseModel):
    id: UUID
    tenant_id: UUID | None
    scope: str
    status: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    findings: list[TenantAuditFinding] = Field(default_factory=list)
    created_at: datetime
