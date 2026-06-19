from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from prepos.api.deps import get_exam_uow
from prepos.application.exam.dto import (
    ConceptAncestorsResponse,
    ConceptDescendantsResponse,
    ConceptResponse,
    PaginatedConceptsResponse,
)
from prepos.application.exam.use_cases import (
    GetConceptAncestorsUseCase,
    GetConceptDescendantsUseCase,
    GetConceptUseCase,
    SearchConceptsUseCase,
)
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork

router = APIRouter(prefix="/concepts", tags=["Concepts"])


def get_concept_use_case(
    uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
) -> GetConceptUseCase:
    return GetConceptUseCase(uow)


def get_ancestors_use_case(
    uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
) -> GetConceptAncestorsUseCase:
    return GetConceptAncestorsUseCase(uow)


def get_descendants_use_case(
    uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
) -> GetConceptDescendantsUseCase:
    return GetConceptDescendantsUseCase(uow)


def get_search_use_case(
    uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
) -> SearchConceptsUseCase:
    return SearchConceptsUseCase(uow)


@router.get("/search", response_model=PaginatedConceptsResponse, summary="Search concepts")
async def search_concepts(
    use_case: Annotated[SearchConceptsUseCase, Depends(get_search_use_case)],
    exam_id: str = Query(default="upsc_cse"),
    q: str | None = Query(default=None, alias="query"),
    subject_id: str | None = Query(default=None),
    topic_id: str | None = Query(default=None),
    status: str | None = Query(default="active"),
    catalog_version: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginatedConceptsResponse:
    return await use_case.execute(
        exam_id=exam_id,
        query=q,
        subject_id=subject_id,
        topic_id=topic_id,
        status=status,
        catalog_version=catalog_version,
        offset=offset,
        limit=limit,
    )


@router.get("/{concept_id}", response_model=ConceptResponse, summary="Get concept by ID")
async def get_concept(
    concept_id: str,
    use_case: Annotated[GetConceptUseCase, Depends(get_concept_use_case)],
) -> ConceptResponse:
    return await use_case.execute(concept_id)


@router.get("/{concept_id}/ancestors", response_model=ConceptAncestorsResponse, summary="Get concept ancestors")
async def get_concept_ancestors(
    concept_id: str,
    use_case: Annotated[GetConceptAncestorsUseCase, Depends(get_ancestors_use_case)],
) -> ConceptAncestorsResponse:
    return await use_case.execute(concept_id)


@router.get(
    "/{concept_id}/descendants",
    response_model=ConceptDescendantsResponse,
    summary="Get concept descendants",
)
async def get_concept_descendants(
    concept_id: str,
    use_case: Annotated[GetConceptDescendantsUseCase, Depends(get_descendants_use_case)],
) -> ConceptDescendantsResponse:
    return await use_case.execute(concept_id)
