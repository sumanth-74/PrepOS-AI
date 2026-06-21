from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from prepos.api.deps import (
    get_current_context,
    get_disaster_recovery_service,
    get_evaluation_platform_service,
    get_forecast_accuracy_service,
    get_job_reliability_service,
    get_knowledge_security_service,
    get_monitoring_service,
    get_outcome_measurement_service,
    get_platform_readiness_service,
    get_product_analytics_service,
    get_prompt_security_service,
    get_recommendation_validation_service,
    get_tenant_audit_service,
    get_platform_maturity_repo,
)
from prepos.application.platform.evaluation_platform_service import QuestionLabelRequest
from prepos.application.security.models import (
    PromptSecurityDashboardResponse,
    PromptSecurityEventRecord,
    TenantAuditReportRecord,
)
from prepos.core.tenancy import RoleName, TenantContext

security_router = APIRouter(prefix="/admin/security", tags=["Admin Security"])
jobs_router = APIRouter(prefix="/admin/jobs", tags=["Admin Jobs"])
evaluations_router = APIRouter(prefix="/admin/evaluations", tags=["Admin Evaluations"])
forecast_accuracy_router = APIRouter(prefix="/admin/forecast-accuracy", tags=["Admin Forecast Accuracy"])
recommendation_validation_router = APIRouter(
    prefix="/admin/recommendation-validation",
    tags=["Admin Recommendation Validation"],
)
monitoring_router = APIRouter(prefix="/admin/monitoring", tags=["Admin Monitoring"])
disaster_recovery_router = APIRouter(prefix="/admin/disaster-recovery", tags=["Admin Disaster Recovery"])
adoption_router = APIRouter(prefix="/admin/adoption", tags=["Admin Adoption"])
outcomes_router = APIRouter(prefix="/admin/outcomes", tags=["Admin Outcomes"])
platform_readiness_router = APIRouter(prefix="/admin/platform-readiness", tags=["Admin Platform Readiness"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


class PromptSecurityListResponse(BaseModel):
    items: list[PromptSecurityEventRecord]
    total: int
    dashboard: PromptSecurityDashboardResponse


class TenantAuditListResponse(BaseModel):
    items: list[TenantAuditReportRecord]
    total: int


class KnowledgeSecurityListResponse(BaseModel):
    items: list[dict]
    total: int
    dashboard: dict


class RunAuditRequest(BaseModel):
    scope: str = "full"


class ForecastAccuracyRecordRequest(BaseModel):
    student_id: UUID
    exam_id: str
    predicted_readiness: float
    actual_readiness: float
    forecast_id: UUID | None = None


class RecommendationValidationRequest(BaseModel):
    student_id: UUID
    event_type: str
    recommendation_id: UUID | None = None
    predicted_gain: float | None = None
    actual_gain: float | None = None
    is_control: bool = False


@security_router.get("", response_model=PromptSecurityListResponse)
async def get_security_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_prompt_security_service)],
    limit: int = 50,
    offset: int = 0,
) -> PromptSecurityListResponse:
    _require_admin(context)
    dashboard = await service.get_dashboard(tenant_id=context.tenant_id)
    items, total = await service.list_events(tenant_id=context.tenant_id, limit=limit, offset=offset)
    return PromptSecurityListResponse(items=items, total=total, dashboard=dashboard)


@security_router.get("/tenant-audit", response_model=TenantAuditListResponse)
async def list_tenant_audits(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_tenant_audit_service)],
    limit: int = 20,
    offset: int = 0,
) -> TenantAuditListResponse:
    _require_admin(context)
    items, total = await service.list_reports(tenant_id=context.tenant_id, limit=limit, offset=offset)
    return TenantAuditListResponse(items=items, total=total)


@security_router.post("/tenant-audit/run", response_model=TenantAuditReportRecord)
async def run_tenant_audit(
    body: RunAuditRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_tenant_audit_service)],
) -> TenantAuditReportRecord:
    _require_admin(context)
    return await service.run_audit(tenant_id=context.tenant_id, scope=body.scope)


@security_router.get("/tenant-audit/{report_id}/export")
async def export_tenant_audit(
    report_id: UUID,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_tenant_audit_service)],
) -> PlainTextResponse:
    _require_admin(context)
    csv_content = await service.export_csv(report_id=report_id)
    if not csv_content:
        raise HTTPException(status_code=404, detail="Report not found.")
    return PlainTextResponse(content=csv_content, media_type="text/csv")


@security_router.get("/knowledge", response_model=KnowledgeSecurityListResponse)
async def get_knowledge_security(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_knowledge_security_service)],
    limit: int = 50,
    offset: int = 0,
) -> KnowledgeSecurityListResponse:
    _require_admin(context)
    dashboard = await service.get_dashboard(tenant_id=context.tenant_id)
    items, total = await service.list_scans(tenant_id=context.tenant_id, limit=limit, offset=offset)
    return KnowledgeSecurityListResponse(items=items, total=total, dashboard=dashboard.model_dump())


@security_router.get("/rate-limits")
async def get_rate_limits_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
) -> dict:
    _require_admin(context)
    return await repo.get_rate_limit_dashboard(tenant_id=context.tenant_id, days=30)


@jobs_router.get("")
async def get_jobs_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_job_reliability_service)],
) -> dict:
    _require_admin(context)
    return await service.get_dashboard()


@evaluations_router.get("")
async def get_evaluations_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_evaluation_platform_service)],
    limit: int = 50,
    offset: int = 0,
) -> dict:
    _require_admin(context)
    dashboard = await service.get_dashboard(tenant_id=context.tenant_id)
    questions, total = await service.list_questions(tenant_id=context.tenant_id, limit=limit, offset=offset)
    return {"dashboard": dashboard, "questions": questions, "total": total}


@evaluations_router.post("/label")
async def label_evaluation_question(
    body: QuestionLabelRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_evaluation_platform_service)],
) -> dict:
    _require_admin(context)
    role = "faculty" if RoleName.FACULTY in context.roles else "admin"
    label_id = await service.label_question(
        tenant_id=context.tenant_id,
        labeler_id=context.user_id,
        labeler_role=role,
        request=body,
    )
    return {"label_id": str(label_id)}


@forecast_accuracy_router.get("")
async def get_forecast_accuracy_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_forecast_accuracy_service)],
    days: int = 90,
) -> dict:
    _require_admin(context)
    return await service.get_dashboard(tenant_id=context.tenant_id, days=days)


@forecast_accuracy_router.post("/record")
async def record_forecast_accuracy(
    body: ForecastAccuracyRecordRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_forecast_accuracy_service)],
) -> dict:
    _require_admin(context)
    event_id = await service.record_accuracy(
        tenant_id=context.tenant_id,
        student_id=body.student_id,
        exam_id=body.exam_id,
        predicted_readiness=body.predicted_readiness,
        actual_readiness=body.actual_readiness,
        forecast_id=body.forecast_id,
    )
    return {"event_id": str(event_id)}


@recommendation_validation_router.get("")
async def get_recommendation_validation_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_recommendation_validation_service)],
    days: int = 90,
) -> dict:
    _require_admin(context)
    return await service.get_dashboard(tenant_id=context.tenant_id, days=days)


@recommendation_validation_router.post("/record")
async def record_recommendation_validation(
    body: RecommendationValidationRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_recommendation_validation_service)],
) -> dict:
    _require_admin(context)
    event_id = await service.record_event(
        tenant_id=context.tenant_id,
        student_id=body.student_id,
        event_type=body.event_type,
        recommendation_id=body.recommendation_id,
        predicted_gain=body.predicted_gain,
        actual_gain=body.actual_gain,
        is_control=body.is_control,
    )
    return {"event_id": str(event_id)}


@monitoring_router.get("")
async def get_monitoring_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_monitoring_service)],
) -> dict:
    _require_admin(context)
    return await service.get_dashboard()


@disaster_recovery_router.get("")
async def get_disaster_recovery_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_disaster_recovery_service)],
) -> dict:
    _require_admin(context)
    return await service.get_dashboard()


@disaster_recovery_router.post("/verify")
async def run_disaster_recovery_verification(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_disaster_recovery_service)],
) -> dict:
    _require_admin(context)
    return await service.verify_all()


@adoption_router.get("")
async def get_adoption_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_product_analytics_service)],
) -> dict:
    _require_admin(context)
    return await service.get_dashboard(tenant_id=context.tenant_id)


@outcomes_router.get("")
async def get_outcomes_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_outcome_measurement_service)],
) -> dict:
    _require_admin(context)
    return await service.get_dashboard(tenant_id=context.tenant_id)


@platform_readiness_router.get("")
async def get_platform_readiness(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_platform_readiness_service)],
) -> dict:
    _require_admin(context)
    latest = await service.get_latest()
    if latest is None:
        return await service.compute_score(tenant_id=context.tenant_id)
    return latest


@platform_readiness_router.post("/compute")
async def compute_platform_readiness(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_platform_readiness_service)],
) -> dict:
    _require_admin(context)
    return await service.compute_score(tenant_id=context.tenant_id)
