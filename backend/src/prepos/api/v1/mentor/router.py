from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from prepos.api.deps import (
    get_current_context,
    get_mentor_case_read_service,
    get_mentor_case_service,
    get_mentor_queue_read_service,
)
from prepos.application.mentor.mentor_case_read_service import MentorCaseReadService, MentorQueueReadService
from prepos.application.mentor.mentor_case_service import MentorCaseService
from prepos.application.mentor.mentor_dto import (
    AddCaseNoteRequest,
    MentorCaseResponse,
    MentorDashboardResponse,
    MentorQueueItemResponse,
    ResolveCaseRequest,
)
from prepos.core.exceptions import DomainError
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.mentor.mentor_types_v1 import CaseResolutionReason, CaseStatus

router = APIRouter(prefix="/mentor", tags=["Mentor Operations"])


def _require_mentor_role(context: TenantContext) -> None:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)


@router.get(
    "/queue",
    response_model=list[MentorQueueItemResponse],
    summary="Prioritized mentor action queue",
)
async def get_mentor_queue(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorQueueReadService, Depends(get_mentor_queue_read_service)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[MentorQueueItemResponse]:
    _require_mentor_role(context)
    response = await service.list_queue(
        tenant_id=context.tenant_id,
        limit=limit,
    )
    return response.items


@router.get(
    "/dashboard",
    response_model=MentorDashboardResponse,
    summary="Mentor workspace dashboard",
)
async def get_mentor_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorCaseReadService, Depends(get_mentor_case_read_service)],
) -> MentorDashboardResponse:
    _require_mentor_role(context)
    return await service.get_dashboard(tenant_id=context.tenant_id)


@router.get(
    "/cases/{case_id}",
    response_model=MentorCaseResponse,
    summary="Get mentor case detail",
)
async def get_mentor_case(
    case_id: UUID,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorCaseReadService, Depends(get_mentor_case_read_service)],
) -> MentorCaseResponse:
    _require_mentor_role(context)
    return await service.get_case(tenant_id=context.tenant_id, case_id=case_id)


@router.get(
    "/cases",
    response_model=list[MentorCaseResponse],
    summary="List mentor cases",
)
async def list_mentor_cases(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorCaseReadService, Depends(get_mentor_case_read_service)],
    status: CaseStatus | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[MentorCaseResponse]:
    _require_mentor_role(context)
    return await service.list_cases(
        tenant_id=context.tenant_id,
        status=status,
        limit=limit,
    )


@router.post(
    "/cases/{case_id}/notes",
    response_model=MentorCaseResponse,
    summary="Add a note to a mentor case",
)
async def add_case_note(
    case_id: UUID,
    body: AddCaseNoteRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    write_service: Annotated[MentorCaseService, Depends(get_mentor_case_service)],
    read_service: Annotated[MentorCaseReadService, Depends(get_mentor_case_read_service)],
) -> MentorCaseResponse:
    _require_mentor_role(context)
    updated = await write_service.add_case_note(
        tenant_id=context.tenant_id,
        case_id=case_id,
        mentor_id=context.user_id,
        note=body.note,
        correlation_id=context.correlation_id or str(case_id),
        causation_id=str(case_id),
    )
    if updated is None:
        raise DomainError("Mentor case not found.", details={"case_id": str(case_id)})
    return await read_service.get_case(tenant_id=context.tenant_id, case_id=case_id)


@router.post(
    "/cases/{case_id}/resolve",
    response_model=MentorCaseResponse,
    summary="Resolve a mentor case",
)
async def resolve_case(
    case_id: UUID,
    body: ResolveCaseRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    write_service: Annotated[MentorCaseService, Depends(get_mentor_case_service)],
    read_service: Annotated[MentorCaseReadService, Depends(get_mentor_case_read_service)],
) -> MentorCaseResponse:
    _require_mentor_role(context)
    try:
        resolution_reason = CaseResolutionReason(body.resolution_reason)
    except ValueError as exc:
        raise DomainError(
            "Invalid resolution reason.",
            details={"resolution_reason": body.resolution_reason},
        ) from exc
    resolved = await write_service.resolve_case(
        tenant_id=context.tenant_id,
        case_id=case_id,
        resolution_reason=resolution_reason,
        correlation_id=context.correlation_id or str(case_id),
        causation_id=str(case_id),
    )
    if resolved is None:
        raise DomainError("Mentor case not found.", details={"case_id": str(case_id)})
    return await read_service.get_case(tenant_id=context.tenant_id, case_id=case_id)
