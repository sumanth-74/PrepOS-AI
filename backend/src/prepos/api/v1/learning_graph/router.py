from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from prepos.api.deps import (
    get_current_context,
    get_learning_graph_activity_service,
    get_learning_graph_read_service,
    get_revision_queue_read_service,
    get_student_uow,
)
from prepos.application.learning_graph.activity_service import LearningGraphActivityService
from prepos.application.learning_graph.dto import (
    ConceptProgressNodeResponse,
    DueRevisionItemResponse,
    LearningGraphActivityResponse,
    LearningGraphOverviewResponse,
    LearningGraphReadinessResponse,
    LearningGraphSummaryResponse,
    LearningGraphWeaknessesResponse,
    RecordAssessmentRequest,
    RecordPyqChangeRequest,
    RecordRevisionRequest,
    RecordStudySessionRequest,
)
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.revision_queue.dto import RevisionQueueItemResponse
from prepos.application.revision_queue.read_service import RevisionQueueReadService
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.learning_graph.exceptions import NodeNotFoundError
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork

router = APIRouter(prefix="/learning-graph", tags=["Learning Graph"])


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


@router.get("", response_model=LearningGraphOverviewResponse, summary="Learning graph overview")
async def get_learning_graph_overview(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> LearningGraphOverviewResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.get_overview(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        limit=limit,
    )


@router.get("/summary", response_model=LearningGraphSummaryResponse, summary="Student graph summary")
async def get_learning_graph_summary(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> LearningGraphSummaryResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.get_summary(tenant_id=context.tenant_id, student_id=target_student_id)


@router.get(
    "/nodes/{concept_id}",
    response_model=ConceptProgressNodeResponse,
    summary="Get concept progress node",
)
async def get_learning_graph_node(
    concept_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> ConceptProgressNodeResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.get_node(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        concept_id=concept_id,
    )


@router.get("/weaknesses", response_model=LearningGraphWeaknessesResponse, summary="Weakest concepts")
async def get_learning_graph_weaknesses(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
) -> LearningGraphWeaknessesResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.get_weaknesses(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        limit=limit,
    )


@router.get(
    "/revisions/due",
    response_model=list[DueRevisionItemResponse],
    summary="Concepts due for revision",
)
async def get_due_revisions(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DueRevisionItemResponse]:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.list_due_revisions(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        limit=limit,
    )


@router.get(
    "/revisions/queue",
    response_model=list[RevisionQueueItemResponse],
    summary="Persisted revision queue projection",
)
async def get_revision_queue(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[RevisionQueueReadService, Depends(get_revision_queue_read_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[RevisionQueueItemResponse]:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.list_queue(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        limit=limit,
    )


@router.get(
    "/readiness",
    response_model=LearningGraphReadinessResponse,
    summary="Student exam readiness score",
)
async def get_learning_graph_readiness(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> LearningGraphReadinessResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.get_readiness(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
    )


@router.post(
    "/activities/assessment",
    response_model=LearningGraphActivityResponse,
    status_code=202,
    summary="Record completed assessment via outbox",
)
async def record_assessment(
    body: RecordAssessmentRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    activity_service: Annotated[LearningGraphActivityService, Depends(get_learning_graph_activity_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> LearningGraphActivityResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    await activity_service.publish_assessment_completed(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        exam_id=body.exam_id,
        concept_id=body.concept_id,
        mcq_correct=body.mcq_correct,
        self_confidence=body.self_confidence,
        correlation_id=context.correlation_id or str(target_student_id),
        causation_id=None,
    )
    return LearningGraphActivityResponse(event_type="AssessmentCompleted")


@router.post(
    "/activities/revision",
    response_model=LearningGraphActivityResponse,
    status_code=202,
    summary="Record completed revision via outbox",
)
async def record_revision(
    body: RecordRevisionRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    activity_service: Annotated[LearningGraphActivityService, Depends(get_learning_graph_activity_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> LearningGraphActivityResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    await activity_service.publish_revision_completed(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        exam_id=body.exam_id,
        concept_id=body.concept_id,
        recall_grade=body.recall_grade,
        correlation_id=context.correlation_id or str(target_student_id),
        causation_id=None,
    )
    return LearningGraphActivityResponse(event_type="RevisionCompleted")


@router.post(
    "/activities/study-session",
    response_model=LearningGraphActivityResponse,
    status_code=202,
    summary="Record study session via outbox",
)
async def record_study_session(
    body: RecordStudySessionRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    activity_service: Annotated[LearningGraphActivityService, Depends(get_learning_graph_activity_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> LearningGraphActivityResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    await activity_service.publish_study_session_logged(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        exam_id=body.exam_id,
        concept_id=body.concept_id,
        engaged_minutes=body.engaged_minutes,
        correlation_id=context.correlation_id or str(target_student_id),
        causation_id=None,
    )
    return LearningGraphActivityResponse(event_type="StudySessionLogged")


@router.post(
    "/activities/pyq-change",
    response_model=LearningGraphActivityResponse,
    status_code=202,
    summary="Record PYQ importance change via outbox",
)
async def record_pyq_change(
    body: RecordPyqChangeRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    activity_service: Annotated[LearningGraphActivityService, Depends(get_learning_graph_activity_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> LearningGraphActivityResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    await activity_service.publish_pyq_data_changed(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        exam_id=body.exam_id,
        concept_id=body.concept_id,
        global_importance=body.global_importance,
        correlation_id=context.correlation_id or str(target_student_id),
        causation_id=None,
    )
    return LearningGraphActivityResponse(event_type="PYQDataChanged")
