from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from prepos.api.deps import get_current_context, get_knowledge_admin_service
from prepos.application.knowledge.dto import KnowledgeIndexingMetricsResponse
from prepos.application.knowledge.services import KnowledgeAdminService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/knowledge", tags=["Admin Knowledge"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get(
    "/metrics",
    response_model=KnowledgeIndexingMetricsResponse,
    summary="Knowledge indexing and failure metrics",
)
async def get_knowledge_metrics(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[KnowledgeAdminService, Depends(get_knowledge_admin_service)],
) -> KnowledgeIndexingMetricsResponse:
    _require_admin(context)
    return await service.get_indexing_metrics(tenant_id=context.tenant_id)
