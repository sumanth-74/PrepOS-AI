from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from prepos.api.deps import (
    get_current_context,
    get_student_uow,
    get_twin_read_service,
    get_twin_recommendation_service,
    get_twin_snapshot_read_service,
)
from prepos.application.twin.dto import TwinRecommendationResponse
from prepos.application.twin.services import TwinRecommendationService
from prepos.application.twin.snapshot_dto import TwinSnapshotResponse
from prepos.application.twin.snapshot_read_service import TwinSnapshotReadService
from prepos.application.twin.twin_dto import TwinDashboardResponse, TwinProjectionMetricsResponse, TwinResponse
from prepos.application.twin.twin_read_service import TwinReadService
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.learning_graph.exceptions import NodeNotFoundError
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork

router = APIRouter(prefix="/twin", tags=["Preparation Twin"])


async def _resolve_student_id(
    context: TenantContext,
    student_uow: SqlAlchemyStudentUnitOfWork,
    student_id: UUID | None,
) -> UUID:
    if student_id is not None:
        student = await student_uow.student_repo.get_by_id(context.tenant_id, student_id)
        if student is None:
            raise NodeNotFoundError(
                "Student not found.",
                details={"student_id": str(student_id)},
            )
        if RoleName.STUDENT in context.roles and student.user_id != context.user_id:
            raise NodeNotFoundError(
                "Student access denied.",
                details={"student_id": str(student_id)},
            )
        return student.id

    student = await student_uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
    if student is None:
        raise NodeNotFoundError(
            "Student profile not found.",
            details={"user_id": str(context.user_id)},
        )
    return student.id


@router.get(
    "/recommendations",
    response_model=list[TwinRecommendationResponse],
    summary="Prioritized study recommendations",
)
async def get_twin_recommendations(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[TwinRecommendationService, Depends(get_twin_recommendation_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[TwinRecommendationResponse]:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.list_recommendations(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        limit=limit,
    )


@router.get(
    "",
    response_model=TwinResponse,
    summary="Canonical Preparation Twin projection",
)
async def get_twin(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[TwinReadService, Depends(get_twin_read_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> TwinResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.get_twin(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
    )


@router.get(
    "/dashboard",
    response_model=TwinDashboardResponse,
    summary="Lightweight Twin dashboard read model",
)
async def get_twin_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[TwinReadService, Depends(get_twin_read_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> TwinDashboardResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.get_dashboard(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
    )


@router.get(
    "/metrics",
    response_model=TwinProjectionMetricsResponse,
    summary="Internal Twin projection metrics",
    include_in_schema=True,
)
async def get_twin_metrics(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[TwinReadService, Depends(get_twin_read_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> TwinProjectionMetricsResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.get_metrics(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
    )


@router.get(
    "/snapshot",
    response_model=TwinSnapshotResponse,
    summary="Persisted Twin snapshot projection (deprecated)",
    deprecated=True,
)
async def get_twin_snapshot(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[TwinSnapshotReadService, Depends(get_twin_snapshot_read_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> TwinSnapshotResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.get_snapshot(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
    )
