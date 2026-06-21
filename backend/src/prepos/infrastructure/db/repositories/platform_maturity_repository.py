from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.security.models import (
    KnowledgeSecurityDashboardResponse,
    PromptSecurityDashboardResponse,
    PromptSecurityEventRecord,
    TenantAuditFinding,
    TenantAuditReportRecord,
)
from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.infrastructure.db.models.platform_maturity import (
    BackgroundJobEventModel,
    BackupVerificationEventModel,
    DomainEventStreamLogModel,
    ForecastAccuracyEventModel,
    KnowledgeSecurityScanModel,
    PlatformReadinessScoreModel,
    ProductAnalyticsSnapshotModel,
    PromptSecurityEventModel,
    QuestionLabelModel,
    RateLimitEventModel,
    RealUserQuestionModel,
    RecommendationValidationEventModel,
    TenantAuditReportModel,
)


class SqlAlchemyPlatformMaturityRepository(PlatformMaturityRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
    ) -> UUID:
        event_id = uuid4()
        self._session.add(
            PromptSecurityEventModel(
                id=event_id,
                tenant_id=tenant_id,
                user_id=user_id,
                source=source,
                prompt_text=prompt_text,
                risk_score=risk_score,
                risk_level=risk_level,
                attack_categories=attack_categories,
                blocked=blocked,
                blocked_reason=blocked_reason,
                trace_id=trace_id,
                created_at=now,
            )
        )
        await self._session.flush()
        return event_id

    async def get_prompt_security_dashboard(
        self,
        *,
        tenant_id: UUID | None,
        days: int,
    ) -> PromptSecurityDashboardResponse:
        since = datetime.now(UTC) - timedelta(days=days)
        stmt = select(PromptSecurityEventModel).where(PromptSecurityEventModel.created_at >= since)
        if tenant_id is not None:
            stmt = stmt.where(PromptSecurityEventModel.tenant_id == tenant_id)
        rows = (await self._session.scalars(stmt)).all()
        categories: dict[str, int] = {}
        tenant_dist: dict[str, int] = {}
        blocked = 0
        for row in rows:
            if row.blocked:
                blocked += 1
            tid = str(row.tenant_id)
            tenant_dist[tid] = tenant_dist.get(tid, 0) + 1
            for cat in row.attack_categories or []:
                categories[cat] = categories.get(cat, 0) + 1
        return PromptSecurityDashboardResponse(
            total_attacks=len(rows),
            blocked_attacks=blocked,
            attack_categories=categories,
            tenant_distribution=tenant_dist,
        )

    async def list_prompt_security_events(
        self,
        *,
        tenant_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[PromptSecurityEventRecord], int]:
        count_stmt = select(func.count(PromptSecurityEventModel.id))
        stmt = select(PromptSecurityEventModel).order_by(PromptSecurityEventModel.created_at.desc())
        if tenant_id is not None:
            count_stmt = count_stmt.where(PromptSecurityEventModel.tenant_id == tenant_id)
            stmt = stmt.where(PromptSecurityEventModel.tenant_id == tenant_id)
        total = int(await self._session.scalar(count_stmt) or 0)
        rows = (await self._session.scalars(stmt.limit(limit).offset(offset))).all()
        return [_to_prompt_event(row) for row in rows], total

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
    ) -> UUID:
        scan_id = uuid4()
        self._session.add(
            KnowledgeSecurityScanModel(
                id=scan_id,
                tenant_id=tenant_id,
                source_id=source_id,
                risk_score=risk_score,
                risk_level=risk_level,
                attack_categories=attack_categories,
                flagged=flagged,
                scan_status=scan_status,
                details_json=details,
                created_at=now,
            )
        )
        await self._session.flush()
        return scan_id

    async def get_knowledge_security_dashboard(
        self,
        *,
        tenant_id: UUID | None,
    ) -> KnowledgeSecurityDashboardResponse:
        stmt = select(KnowledgeSecurityScanModel)
        if tenant_id is not None:
            stmt = stmt.where(KnowledgeSecurityScanModel.tenant_id == tenant_id)
        rows = (await self._session.scalars(stmt)).all()
        categories: dict[str, int] = {}
        flagged = 0
        quarantined = 0
        for row in rows:
            if row.flagged:
                flagged += 1
            if row.scan_status == "quarantined":
                quarantined += 1
            for cat in row.attack_categories or []:
                categories[cat] = categories.get(cat, 0) + 1
        return KnowledgeSecurityDashboardResponse(
            total_scans=len(rows),
            flagged_sources=flagged,
            quarantined_sources=quarantined,
            attack_categories=categories,
        )

    async def list_knowledge_security_scans(
        self,
        *,
        tenant_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict], int]:
        count_stmt = select(func.count(KnowledgeSecurityScanModel.id))
        stmt = select(KnowledgeSecurityScanModel).order_by(KnowledgeSecurityScanModel.created_at.desc())
        if tenant_id is not None:
            count_stmt = count_stmt.where(KnowledgeSecurityScanModel.tenant_id == tenant_id)
            stmt = stmt.where(KnowledgeSecurityScanModel.tenant_id == tenant_id)
        total = int(await self._session.scalar(count_stmt) or 0)
        rows = (await self._session.scalars(stmt.limit(limit).offset(offset))).all()
        items = [
            {
                "id": str(row.id),
                "source_id": str(row.source_id),
                "risk_score": row.risk_score,
                "risk_level": row.risk_level,
                "attack_categories": row.attack_categories,
                "flagged": row.flagged,
                "scan_status": row.scan_status,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
        return items, total

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
    ) -> UUID:
        report_id = uuid4()
        self._session.add(
            TenantAuditReportModel(
                id=report_id,
                tenant_id=tenant_id,
                scope=scope,
                status=status,
                total_checks=total_checks,
                passed_checks=passed_checks,
                failed_checks=failed_checks,
                findings_json=findings,
                created_at=now,
            )
        )
        await self._session.flush()
        return report_id

    async def list_tenant_audit_reports(
        self,
        *,
        tenant_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[TenantAuditReportRecord], int]:
        count_stmt = select(func.count(TenantAuditReportModel.id))
        stmt = select(TenantAuditReportModel).order_by(TenantAuditReportModel.created_at.desc())
        if tenant_id is not None:
            count_stmt = count_stmt.where(TenantAuditReportModel.tenant_id == tenant_id)
            stmt = stmt.where(TenantAuditReportModel.tenant_id == tenant_id)
        total = int(await self._session.scalar(count_stmt) or 0)
        rows = (await self._session.scalars(stmt.limit(limit).offset(offset))).all()
        return [_to_audit_report(row) for row in rows], total

    async def get_tenant_audit_report(self, report_id: UUID) -> TenantAuditReportRecord | None:
        row = await self._session.get(TenantAuditReportModel, report_id)
        if row is None:
            return None
        return _to_audit_report(row)

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
    ) -> UUID:
        event_id = uuid4()
        self._session.add(
            RateLimitEventModel(
                id=event_id,
                tenant_id=tenant_id,
                user_id=user_id,
                endpoint_group=endpoint_group,
                request_count=request_count,
                limit_value=limit_value,
                blocked=blocked,
                created_at=now,
            )
        )
        await self._session.flush()
        return event_id

    async def get_rate_limit_dashboard(self, *, tenant_id: UUID | None, days: int) -> dict:
        since = datetime.now(UTC) - timedelta(days=days)
        stmt = select(RateLimitEventModel).where(RateLimitEventModel.created_at >= since)
        if tenant_id is not None:
            stmt = stmt.where(RateLimitEventModel.tenant_id == tenant_id)
        rows = (await self._session.scalars(stmt)).all()
        by_group: dict[str, int] = {}
        blocked = 0
        for row in rows:
            by_group[row.endpoint_group] = by_group.get(row.endpoint_group, 0) + 1
            if row.blocked:
                blocked += 1
        return {
            "total_events": len(rows),
            "blocked_requests": blocked,
            "by_endpoint_group": by_group,
        }

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
    ) -> UUID:
        event_id = uuid4()
        self._session.add(
            BackgroundJobEventModel(
                id=event_id,
                tenant_id=tenant_id,
                task_name=task_name,
                task_id=task_id,
                status=status,
                retry_count=retry_count,
                idempotency_key=idempotency_key,
                error_message=error_message,
                metadata_json=metadata,
                created_at=now,
            )
        )
        await self._session.flush()
        return event_id

    async def get_job_dashboard(self) -> dict:
        rows = (await self._session.scalars(select(BackgroundJobEventModel))).all()
        failed = sum(1 for r in rows if r.status == "failed")
        retrying = sum(1 for r in rows if r.status == "retrying")
        dead_letter = sum(1 for r in rows if r.status == "dead_letter")
        return {
            "total_events": len(rows),
            "failed": failed,
            "retrying": retrying,
            "dead_letter": dead_letter,
        }

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
    ) -> UUID:
        question_id = uuid4()
        self._session.add(
            RealUserQuestionModel(
                id=question_id,
                tenant_id=tenant_id,
                user_id=user_id,
                persona=persona,
                question_text=question_text,
                intent=intent,
                answer_text=answer_text,
                trace_id=trace_id,
                created_at=now,
            )
        )
        await self._session.flush()
        return question_id

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
    ) -> UUID:
        label_id = uuid4()
        self._session.add(
            QuestionLabelModel(
                id=label_id,
                tenant_id=tenant_id,
                question_id=question_id,
                labeler_id=labeler_id,
                labeler_role=labeler_role,
                label=label,
                notes=notes,
                created_at=now,
            )
        )
        await self._session.flush()
        return label_id

    async def list_evaluation_questions(
        self,
        *,
        tenant_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[dict], int]:
        count_stmt = select(func.count(RealUserQuestionModel.id)).where(
            RealUserQuestionModel.tenant_id == tenant_id
        )
        stmt = (
            select(RealUserQuestionModel)
            .where(RealUserQuestionModel.tenant_id == tenant_id)
            .order_by(RealUserQuestionModel.created_at.desc())
        )
        total = int(await self._session.scalar(count_stmt) or 0)
        rows = (await self._session.scalars(stmt.limit(limit).offset(offset))).all()
        items = [
            {
                "id": str(row.id),
                "persona": row.persona,
                "question_text": row.question_text,
                "intent": row.intent,
                "answer_text": row.answer_text,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
        return items, total

    async def get_evaluation_dashboard(self, *, tenant_id: UUID) -> dict:
        questions = (
            await self._session.scalars(
                select(RealUserQuestionModel).where(RealUserQuestionModel.tenant_id == tenant_id)
            )
        ).all()
        labels = (
            await self._session.scalars(
                select(QuestionLabelModel).where(QuestionLabelModel.tenant_id == tenant_id)
            )
        ).all()
        label_counts: dict[str, int] = {}
        for label in labels:
            label_counts[label.label] = label_counts.get(label.label, 0) + 1
        return {
            "total_questions": len(questions),
            "total_labels": len(labels),
            "label_distribution": label_counts,
        }

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
    ) -> UUID:
        abs_error = abs(predicted_readiness - actual_readiness)
        pct_error = (abs_error / actual_readiness * 100.0) if actual_readiness > 0 else 0.0
        within_tolerance = abs_error <= 5.0
        event_id = uuid4()
        self._session.add(
            ForecastAccuracyEventModel(
                id=event_id,
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                predicted_readiness=predicted_readiness,
                actual_readiness=actual_readiness,
                absolute_error=abs_error,
                percentage_error=pct_error,
                within_tolerance=within_tolerance,
                forecast_id=forecast_id,
                created_at=now,
            )
        )
        await self._session.flush()
        return event_id

    async def get_forecast_accuracy_dashboard(self, *, tenant_id: UUID | None, days: int) -> dict:
        since = datetime.now(UTC) - timedelta(days=days)
        stmt = select(ForecastAccuracyEventModel).where(ForecastAccuracyEventModel.created_at >= since)
        if tenant_id is not None:
            stmt = stmt.where(ForecastAccuracyEventModel.tenant_id == tenant_id)
        rows = (await self._session.scalars(stmt)).all()
        if not rows:
            return {"mae": 0.0, "mape": 0.0, "accuracy_pct": 0.0, "total_events": 0, "trend": []}
        mae = sum(r.absolute_error for r in rows) / len(rows)
        mape = sum(r.percentage_error for r in rows) / len(rows)
        accuracy = sum(1 for r in rows if r.within_tolerance) / len(rows) * 100.0
        return {
            "mae": round(mae, 2),
            "mape": round(mape, 2),
            "accuracy_pct": round(accuracy, 2),
            "total_events": len(rows),
            "trend": [{"date": r.created_at.date().isoformat(), "error": r.absolute_error} for r in rows[-30:]],
        }

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
    ) -> UUID:
        event_id = uuid4()
        self._session.add(
            RecommendationValidationEventModel(
                id=event_id,
                tenant_id=tenant_id,
                student_id=student_id,
                recommendation_id=recommendation_id,
                event_type=event_type,
                predicted_gain=predicted_gain,
                actual_gain=actual_gain,
                is_control=is_control,
                metadata_json=metadata,
                created_at=now,
            )
        )
        await self._session.flush()
        return event_id

    async def get_recommendation_validation_dashboard(self, *, tenant_id: UUID | None, days: int) -> dict:
        since = datetime.now(UTC) - timedelta(days=days)
        stmt = select(RecommendationValidationEventModel).where(
            RecommendationValidationEventModel.created_at >= since
        )
        if tenant_id is not None:
            stmt = stmt.where(RecommendationValidationEventModel.tenant_id == tenant_id)
        rows = (await self._session.scalars(stmt)).all()
        shown = sum(1 for r in rows if r.event_type == "shown")
        accepted = sum(1 for r in rows if r.event_type == "accepted")
        completed = sum(1 for r in rows if r.event_type == "completed")
        treatment_gains = [r.actual_gain for r in rows if not r.is_control and r.actual_gain is not None]
        control_gains = [r.actual_gain for r in rows if r.is_control and r.actual_gain is not None]
        avg_treatment = sum(treatment_gains) / len(treatment_gains) if treatment_gains else 0.0
        avg_control = sum(control_gains) / len(control_gains) if control_gains else 0.0
        return {
            "shown": shown,
            "accepted": accepted,
            "completed": completed,
            "acceptance_rate": round(accepted / shown * 100, 2) if shown else 0.0,
            "completion_rate": round(completed / accepted * 100, 2) if accepted else 0.0,
            "avg_treatment_gain": round(avg_treatment, 2),
            "avg_control_gain": round(avg_control, 2),
            "lift": round(avg_treatment - avg_control, 2),
        }

    async def save_backup_verification(
        self,
        *,
        component: str,
        backup_success: bool,
        restore_success: bool | None,
        details: dict,
        now: datetime,
    ) -> UUID:
        event_id = uuid4()
        self._session.add(
            BackupVerificationEventModel(
                id=event_id,
                component=component,
                backup_success=backup_success,
                restore_success=restore_success,
                details_json=details,
                created_at=now,
            )
        )
        await self._session.flush()
        return event_id

    async def get_disaster_recovery_dashboard(self) -> dict:
        rows = (await self._session.scalars(select(BackupVerificationEventModel))).all()
        by_component: dict[str, dict] = {}
        for row in rows:
            by_component[row.component] = {
                "backup_success": row.backup_success,
                "restore_success": row.restore_success,
                "last_checked": row.created_at.isoformat(),
            }
        return {"components": by_component, "total_checks": len(rows)}

    async def save_product_analytics_snapshot(
        self,
        *,
        tenant_id: UUID | None,
        snapshot_date: date,
        metrics: dict,
        now: datetime,
    ) -> UUID:
        snapshot_id = uuid4()
        self._session.add(
            ProductAnalyticsSnapshotModel(
                id=snapshot_id,
                tenant_id=tenant_id,
                snapshot_date=snapshot_date,
                metrics_json=metrics,
                created_at=now,
            )
        )
        await self._session.flush()
        return snapshot_id

    async def get_adoption_dashboard(self, *, tenant_id: UUID | None) -> dict:
        stmt = select(ProductAnalyticsSnapshotModel).order_by(ProductAnalyticsSnapshotModel.snapshot_date.desc())
        if tenant_id is not None:
            stmt = stmt.where(ProductAnalyticsSnapshotModel.tenant_id == tenant_id)
        row = await self._session.scalar(stmt.limit(1))
        if row is None:
            return {
                "weekly_active_users": 0,
                "monthly_active_users": 0,
                "copilot_adoption_pct": 0.0,
                "agent_mode_adoption_pct": 0.0,
                "funnels": {},
            }
        return row.metrics_json

    async def get_outcome_dashboard(self, *, tenant_id: UUID) -> dict:
        forecast = await self.get_forecast_accuracy_dashboard(tenant_id=tenant_id, days=90)
        rec = await self.get_recommendation_validation_dashboard(tenant_id=tenant_id, days=90)
        return {
            "readiness_gain": rec.get("avg_treatment_gain", 0.0),
            "forecast_accuracy_pct": forecast.get("accuracy_pct", 0.0),
            "recommendation_effectiveness": rec.get("lift", 0.0),
            "intervention_roi": 0.0,
            "plan_completion_rate": rec.get("completion_rate", 0.0),
            "student_success_rate": forecast.get("accuracy_pct", 0.0),
        }

    async def get_monitoring_dashboard(self) -> dict:
        from prepos.infrastructure.db.models.agentops import AgentCostModel, AgentTraceModel
        from prepos.infrastructure.db.models.copilot_analytics import CopilotQueryModel

        trace_count = int(await self._session.scalar(select(func.count(AgentTraceModel.id))) or 0)
        cost_rows = (await self._session.scalars(select(AgentCostModel))).all()
        query_count = int(await self._session.scalar(select(func.count(CopilotQueryModel.id))) or 0)
        total_tokens = sum(r.total_tokens for r in cost_rows)
        avg_latency = (
            sum(r.latency_ms for r in (await self._session.scalars(select(AgentTraceModel))).all()) / trace_count
            if trace_count
            else 0
        )
        return {
            "api_query_count": query_count,
            "agent_trace_count": trace_count,
            "avg_agent_latency_ms": round(avg_latency, 2),
            "total_tokens": total_tokens,
            "embedding_failures": 0,
            "rag_latency_ms": 0,
            "queue_latency_ms": 0,
            "forecast_generation_ms": 0,
        }

    async def save_platform_readiness_score(
        self,
        *,
        overall_score: float,
        dimension_scores: dict,
        findings: list[dict],
        now: datetime,
    ) -> UUID:
        score_id = uuid4()
        self._session.add(
            PlatformReadinessScoreModel(
                id=score_id,
                overall_score=overall_score,
                dimension_scores_json=dimension_scores,
                findings_json=findings,
                created_at=now,
            )
        )
        await self._session.flush()
        return score_id

    async def get_latest_platform_readiness(self) -> dict | None:
        row = await self._session.scalar(
            select(PlatformReadinessScoreModel).order_by(PlatformReadinessScoreModel.created_at.desc()).limit(1)
        )
        if row is None:
            return None
        return {
            "overall_score": row.overall_score,
            "dimension_scores": row.dimension_scores_json,
            "findings": row.findings_json,
            "created_at": row.created_at.isoformat(),
        }

    async def save_domain_event_stream_log(
        self,
        *,
        tenant_id: UUID | None,
        event_type: str,
        stream_id: str,
        payload: dict,
        now: datetime,
    ) -> UUID:
        log_id = uuid4()
        self._session.add(
            DomainEventStreamLogModel(
                id=log_id,
                tenant_id=tenant_id,
                event_type=event_type,
                stream_id=stream_id,
                payload_json=payload,
                published_at=now,
            )
        )
        await self._session.flush()
        return log_id


def _to_prompt_event(row: PromptSecurityEventModel) -> PromptSecurityEventRecord:
    return PromptSecurityEventRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        source=row.source,
        risk_score=row.risk_score,
        risk_level=row.risk_level,
        attack_categories=row.attack_categories or [],
        blocked=row.blocked,
        blocked_reason=row.blocked_reason,
        created_at=row.created_at,
    )


def _to_audit_report(row: TenantAuditReportModel) -> TenantAuditReportRecord:
    findings = [TenantAuditFinding.model_validate(f) for f in (row.findings_json or [])]
    return TenantAuditReportRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        scope=row.scope,
        status=row.status,
        total_checks=row.total_checks,
        passed_checks=row.passed_checks,
        failed_checks=row.failed_checks,
        findings=findings,
        created_at=row.created_at,
    )
