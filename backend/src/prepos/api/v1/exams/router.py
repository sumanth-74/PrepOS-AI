from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from prepos.api.deps import get_current_context, get_exam_uow
from prepos.application.exam.dto import CreateExamRequest, ExamResponse
from prepos.application.exam.use_cases import CreateExamUseCase
from prepos.core.tenancy import TenantContext
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork

router = APIRouter(prefix="/exams", tags=["Exams"])


def get_create_exam_use_case(
    uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
) -> CreateExamUseCase:
    return CreateExamUseCase(uow)


@router.get("", response_model=list[ExamResponse], summary="List platform exams")
async def list_exams(
    uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
    status: str | None = Query(default=None),
) -> list[ExamResponse]:
    exams = await uow.exam_repo.list_exams(status=status)
    return [
        ExamResponse(
            exam_id=exam.exam_id,
            exam_code=exam.exam_code,
            exam_name=exam.exam_name,
            exam_type=exam.exam_type.value,
            prelims_weight=exam.prelims_weight,
            mains_weight=exam.mains_weight,
            interview_weight=exam.interview_weight,
            domain_catalog_version=exam.domain_catalog_version,
            essay_included=exam.essay_included,
            status=exam.status.value,
        )
        for exam in exams
    ]


@router.post("", response_model=ExamResponse, status_code=201, summary="Create a new exam catalog root")
async def create_exam(
    body: CreateExamRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    use_case: Annotated[CreateExamUseCase, Depends(get_create_exam_use_case)],
) -> ExamResponse:
    return await use_case.execute(
        context=context,
        exam_id=body.exam_id,
        exam_code=body.exam_code,
        exam_name=body.exam_name,
        exam_type=body.exam_type,
        prelims_weight=body.prelims_weight,
        mains_weight=body.mains_weight,
        interview_weight=body.interview_weight,
        essay_included=body.essay_included,
    )


@router.get("/{exam_id}", response_model=ExamResponse, summary="Get exam by ID")
async def get_exam(
    exam_id: str,
    uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
) -> ExamResponse:
    from prepos.domain.exam.exceptions import ExamNotFoundError

    exam = await uow.exam_repo.get_exam(exam_id)
    if exam is None:
        raise ExamNotFoundError(f"Exam {exam_id} not found.", details={"exam_id": exam_id})
    return ExamResponse(
        exam_id=exam.exam_id,
        exam_code=exam.exam_code,
        exam_name=exam.exam_name,
        exam_type=exam.exam_type.value,
        prelims_weight=exam.prelims_weight,
        mains_weight=exam.mains_weight,
        interview_weight=exam.interview_weight,
        domain_catalog_version=exam.domain_catalog_version,
        essay_included=exam.essay_included,
        status=exam.status.value,
    )
