from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from prepos.api.deps import get_coaching_memory_service, get_current_context
from prepos.application.memory.memory_models import MemoryAdminResponse
from prepos.application.memory.memory_service import CoachingMemoryService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/memory", tags=["Admin Coaching Memory"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("", response_model=MemoryAdminResponse, summary="Coaching memory analytics")
async def get_memory_admin_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
) -> MemoryAdminResponse:
    _require_admin(context)
    return await service.get_admin_dashboard(tenant_id=context.tenant_id)


@router.get("/export", response_class=PlainTextResponse, summary="Export coaching memory CSV")
async def export_memory_csv(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
    user_id: str | None = Query(default=None),
) -> PlainTextResponse:
    _require_admin(context)
    from uuid import UUID

    resolved_user_id = UUID(user_id) if user_id else None
    csv_content = await service.export_csv(tenant_id=context.tenant_id, user_id=resolved_user_id)
    return PlainTextResponse(content=csv_content, media_type="text/csv")
