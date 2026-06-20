from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from prepos.api.deps import (
    get_coaching_memory_service,
    get_current_context,
    get_learning_timeline_service,
    get_student_uow,
)
from prepos.application.memory.memory_models import (
    LearningTimelineResponse,
    MemoryAdminResponse,
    MemoryListResponse,
    MemoryRebuildResponse,
    MilestoneListResponse,
)
from prepos.application.memory.memory_service import CoachingMemoryService, LearningTimelineService
from prepos.core.exceptions import ValidationError
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.learning_graph.exceptions import NodeNotFoundError
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork

router = APIRouter(prefix="/memory", tags=["Coaching Memory"])


@router.get("/student", response_model=MemoryListResponse, summary="List student coaching memories")
async def list_student_memories(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
    memory_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> MemoryListResponse:
    context.require_role(RoleName.STUDENT)
    return await service.list_memories(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        persona="student",
        memory_type=memory_type,
        limit=limit,
    )


@router.get("/student/timeline", response_model=LearningTimelineResponse, summary="Student learning timeline")
async def get_student_timeline(
    context: Annotated[TenantContext, Depends(get_current_context)],
    timeline_service: Annotated[LearningTimelineService, Depends(get_learning_timeline_service)],
    limit: int = Query(default=100, ge=1, le=500),
) -> LearningTimelineResponse:
    context.require_role(RoleName.STUDENT)
    return await timeline_service.get_timeline(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        persona="student",
        limit=limit,
    )


@router.get(
    "/mentor/{student_id}",
    response_model=MemoryListResponse,
    summary="List mentor coaching memories for a student",
)
async def list_mentor_memories(
    student_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    memory_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> MemoryListResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    student = await student_uow.student_repo.get_by_id(context.tenant_id, UUID(student_id))
    if student is None:
        raise ValidationError("Student not found.", details={"student_id": student_id})
    return await service.list_memories(
        tenant_id=context.tenant_id,
        user_id=student.user_id,
        persona="mentor",
        memory_type=memory_type,
        limit=limit,
    )


@router.get("/milestones", response_model=MilestoneListResponse, summary="List progress milestones")
async def list_milestones(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> MilestoneListResponse:
    if context.has_role(RoleName.STUDENT):
        return await service.get_milestones(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            limit=limit,
        )
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    if student_id is None:
        raise ValidationError("student_id is required for mentor milestone requests.")
    student = await student_uow.student_repo.get_by_id(context.tenant_id, UUID(student_id))
    if student is None:
        raise ValidationError("Student not found.", details={"student_id": student_id})
    return await service.get_milestones(
        tenant_id=context.tenant_id,
        user_id=student.user_id,
        limit=limit,
    )


@router.post("/rebuild", response_model=MemoryRebuildResponse, summary="Rebuild coaching memories (admin)")
async def rebuild_memories(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    user_id: str | None = Query(default=None),
    persona: str = Query(default="student"),
) -> MemoryRebuildResponse:
    context.require_role(RoleName.INSTITUTE_ADMIN)
    if user_id is None:
        raise ValidationError("user_id is required for memory rebuild.")
    target_user_id = UUID(user_id)
    student = await student_uow.student_repo.get_by_user_id(context.tenant_id, target_user_id)
    if student is None:
        raise NodeNotFoundError("Student profile not found for user.", details={"user_id": user_id})
    return await service.rebuild_memories(
        tenant_id=context.tenant_id,
        user_id=target_user_id,
        persona=persona,
        student_id=student.id,
    )
