from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from prepos.api.deps import get_current_context, get_exam_uow, get_outbox
from prepos.application.exam.dto import (
    CatalogVersionResponse,
    ExamTreeResponse,
    PublishCatalogRequest,
    SeedImportResponse,
)
from prepos.application.exam.use_cases import (
    GetExamTreeUseCase,
    ImportSeedUseCase,
    PublishCatalogVersionUseCase,
)
from prepos.core.tenancy import TenantContext
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork

router = APIRouter(prefix="/syllabus", tags=["Syllabus"])


def get_exam_tree_use_case(
    uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
) -> GetExamTreeUseCase:
    return GetExamTreeUseCase(uow)


def get_publish_use_case(
    uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
    outbox: Annotated[OutboxPublisher, Depends(get_outbox)],
) -> PublishCatalogVersionUseCase:
    return PublishCatalogVersionUseCase(uow, outbox)


def get_import_seed_use_case(
    uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
) -> ImportSeedUseCase:
    return ImportSeedUseCase(uow)


@router.get("/{exam_id}/tree", response_model=ExamTreeResponse, summary="Get full exam syllabus tree")
async def get_exam_tree(
    exam_id: str,
    use_case: Annotated[GetExamTreeUseCase, Depends(get_exam_tree_use_case)],
    include_draft: bool = Query(default=False),
    catalog_version: str | None = Query(default=None),
) -> ExamTreeResponse:
    return await use_case.execute(
        exam_id,
        include_draft=include_draft,
        catalog_version=catalog_version,
    )


@router.post(
    "/{exam_id}/catalog/versions/{version}/publish",
    response_model=CatalogVersionResponse,
    summary="Publish a catalog version",
)
async def publish_catalog_version(
    exam_id: str,
    version: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    use_case: Annotated[PublishCatalogVersionUseCase, Depends(get_publish_use_case)],
    body: PublishCatalogRequest | None = None,
) -> CatalogVersionResponse:
    return await use_case.execute(
        context=context,
        exam_id=exam_id,
        version=version,
        change_summary=body.change_summary if body else None,
    )


@router.post("/seed/import", response_model=SeedImportResponse, summary="Import UPSC CSE seed catalog")
async def import_seed_catalog(
    context: Annotated[TenantContext, Depends(get_current_context)],
    use_case: Annotated[ImportSeedUseCase, Depends(get_import_seed_use_case)],
) -> SeedImportResponse:
    return await use_case.execute(context=context)
