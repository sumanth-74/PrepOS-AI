from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from uuid import UUID

from prepos.application.security.models import (
    KnowledgeSecurityDashboardResponse,
    PromptSecurityDashboardResponse,
    PromptSecurityEventRecord,
    TenantAuditReportRecord,
)


class PlatformMaturityRepositoryPort(ABC):
    @abstractmethod
    async def save_prompt_security_event(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        source: str,
        prompt_text: str,
        risk_score: float,
        risk_level: str,
        attack_categories: list[str],
        blocked: bool,
        blocked_reason: str | None,
        trace_id: UUID | None,
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def get_prompt_security_dashboard(
        self,
        *,
        tenant_id: UUID | None,
        days: int,
    ) -> PromptSecurityDashboardResponse: ...

    @abstractmethod
    async def list_prompt_security_events(
        self,
        *,
        tenant_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[PromptSecurityEventRecord], int]: ...

    @abstractmethod
    async def save_knowledge_security_scan(
        self,
        *,
        tenant_id: UUID | None,
        source_id: UUID,
        risk_score: float,
        risk_level: str,
        attack_categories: list[str],
        flagged: bool,
        scan_status: str,
        details: dict,
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def get_knowledge_security_dashboard(
        self,
        *,
        tenant_id: UUID | None,
    ) -> KnowledgeSecurityDashboardResponse: ...

    @abstractmethod
    async def list_knowledge_security_scans(
        self,
        *,
        tenant_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict], int]: ...

    @abstractmethod
    async def save_tenant_audit_report(
        self,
        *,
        tenant_id: UUID | None,
        scope: str,
        status: str,
        total_checks: int,
        passed_checks: int,
        failed_checks: int,
        findings: list[dict],
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def list_tenant_audit_reports(
        self,
        *,
        tenant_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[TenantAuditReportRecord], int]: ...

    @abstractmethod
    async def get_tenant_audit_report(self, report_id: UUID) -> TenantAuditReportRecord | None: ...

    @abstractmethod
    async def save_rate_limit_event(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        endpoint_group: str,
        request_count: int,
        limit_value: int,
        blocked: bool,
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def get_rate_limit_dashboard(
        self,
        *,
        tenant_id: UUID | None,
        days: int,
    ) -> dict: ...

    @abstractmethod
    async def save_background_job_event(
        self,
        *,
        tenant_id: UUID | None,
        task_name: str,
        task_id: str,
        status: str,
        retry_count: int,
        idempotency_key: str | None,
        error_message: str | None,
        metadata: dict,
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def get_job_dashboard(self) -> dict: ...

    @abstractmethod
    async def save_real_user_question(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        question_text: str,
        intent: str | None,
        answer_text: str | None,
        trace_id: UUID | None,
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def save_question_label(
        self,
        *,
        tenant_id: UUID,
        question_id: UUID,
        labeler_id: UUID,
        labeler_role: str,
        label: str,
        notes: str | None,
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def list_evaluation_questions(
        self,
        *,
        tenant_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[dict], int]: ...

    @abstractmethod
    async def get_evaluation_dashboard(self, *, tenant_id: UUID) -> dict: ...

    @abstractmethod
    async def save_forecast_accuracy_event(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        predicted_readiness: float,
        actual_readiness: float,
        forecast_id: UUID | None,
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def get_forecast_accuracy_dashboard(
        self,
        *,
        tenant_id: UUID | None,
        days: int,
    ) -> dict: ...

    @abstractmethod
    async def save_recommendation_validation_event(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        recommendation_id: UUID | None,
        event_type: str,
        predicted_gain: float | None,
        actual_gain: float | None,
        is_control: bool,
        metadata: dict,
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def get_recommendation_validation_dashboard(
        self,
        *,
        tenant_id: UUID | None,
        days: int,
    ) -> dict: ...

    @abstractmethod
    async def save_backup_verification(
        self,
        *,
        component: str,
        backup_success: bool,
        restore_success: bool | None,
        details: dict,
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def get_disaster_recovery_dashboard(self) -> dict: ...

    @abstractmethod
    async def save_product_analytics_snapshot(
        self,
        *,
        tenant_id: UUID | None,
        snapshot_date: date,
        metrics: dict,
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def get_adoption_dashboard(self, *, tenant_id: UUID | None) -> dict: ...

    @abstractmethod
    async def get_outcome_dashboard(self, *, tenant_id: UUID) -> dict: ...

    @abstractmethod
    async def get_monitoring_dashboard(self) -> dict: ...

    @abstractmethod
    async def save_platform_readiness_score(
        self,
        *,
        overall_score: float,
        dimension_scores: dict,
        findings: list[dict],
        now: datetime,
    ) -> UUID: ...

    @abstractmethod
    async def get_latest_platform_readiness(self) -> dict | None: ...

    @abstractmethod
    async def save_domain_event_stream_log(
        self,
        *,
        tenant_id: UUID | None,
        event_type: str,
        stream_id: str,
        payload: dict,
        now: datetime,
    ) -> UUID: ...
