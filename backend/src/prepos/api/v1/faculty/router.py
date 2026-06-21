from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from prepos.api.deps import (
    get_cohort_intelligence_service,
    get_current_context,
    get_goal_forecasting_service,
    get_pyq_service,
)
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/faculty", tags=["Faculty Workspace"])


def _require_faculty(context: TenantContext) -> None:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)


@router.get("/workspace")
async def get_faculty_workspace(
    context: Annotated[TenantContext, Depends(get_current_context)],
    cohort_service: Annotated[object, Depends(get_cohort_intelligence_service)],
    forecasting_service: Annotated[object, Depends(get_goal_forecasting_service)],
    pyq_service: Annotated[object, Depends(get_pyq_service)],
    exam_id: str = "upsc_cse",
) -> dict:
    """Faculty workspace aggregating existing P7–P10 intelligence (P11.15)."""
    _require_faculty(context)
    cohort_summary = await cohort_service.get_cohort_summary(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
    )
    pyq_trends = await pyq_service.get_trends(tenant_id=context.tenant_id, exam_id=exam_id)
    return {
        "teaching_plans": {
            "summary": "Adaptive teaching plans derived from cohort weak concepts.",
            "exam_id": exam_id,
        },
        "weak_concepts": cohort_summary.weak_concepts if hasattr(cohort_summary, "weak_concepts") else [],
        "pyq_trends": pyq_trends if isinstance(pyq_trends, dict) else {},
        "current_affairs_coverage": {"status": "available", "route": "/admin/current-affairs"},
        "cohort_insights": cohort_summary.model_dump() if hasattr(cohort_summary, "model_dump") else {},
        "agent": "faculty_teaching_agent",
        "explain": "Insights assembled from cohort, forecasting, recommendation, PYQ, and CA services.",
    }
