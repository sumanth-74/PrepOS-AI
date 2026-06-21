from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from prepos.api.deps import (
    get_current_context,
    get_knowledge_admin_service,
    get_knowledge_agent_service,
    get_knowledge_search_service,
    get_prompt_security_service,
)
from prepos.application.knowledge.dto import (
    CreateKnowledgeSourceRequest,
    KnowledgeAskRequest,
    KnowledgeAskResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
)
from prepos.application.knowledge.knowledge_agent_service import KnowledgeAgentService
from prepos.application.knowledge.services import KnowledgeAdminService, KnowledgeSearchService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Hybrid knowledge retrieval (vector + FTS + RRF)",
)
async def search_knowledge(
    request: KnowledgeSearchRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[KnowledgeSearchService, Depends(get_knowledge_search_service)],
) -> KnowledgeSearchResponse:
    return await service.search(tenant_id=context.tenant_id, request=request)


@router.post(
    "/ask",
    response_model=KnowledgeAskResponse,
    summary="Grounded knowledge Q&A with citations",
)
async def ask_knowledge(
    request: KnowledgeAskRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[KnowledgeAgentService, Depends(get_knowledge_agent_service)],
    prompt_security: Annotated[object, Depends(get_prompt_security_service)],
) -> KnowledgeAskResponse:
    await prompt_security.evaluate_prompt(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        source="knowledge_ask",
        prompt=request.query,
    )
    return await service.ask(tenant_id=context.tenant_id, request=request)


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.post(
    "/sources",
    response_model=KnowledgeSourceResponse,
    summary="Upload and index a knowledge source (admin)",
)
async def create_knowledge_source(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[KnowledgeAdminService, Depends(get_knowledge_admin_service)],
    exam_id: Annotated[str, Form()],
    source_type: Annotated[str, Form()],
    title: Annotated[str, Form()],
    file: UploadFile = File(...),
    catalog_version: Annotated[str | None, Form()] = None,
    subject_id: Annotated[str | None, Form()] = None,
    topic_id: Annotated[str | None, Form()] = None,
    concept_ids: Annotated[str | None, Form()] = None,
) -> KnowledgeSourceResponse:
    _require_admin(context)
    file_bytes = await file.read()
    parsed_concept_ids = [item.strip() for item in (concept_ids or "").split(",") if item.strip()]
    request = CreateKnowledgeSourceRequest(
        exam_id=exam_id,
        source_type=source_type,
        title=title,
        catalog_version=catalog_version,
        subject_id=subject_id,
        topic_id=topic_id,
        concept_ids=parsed_concept_ids,
    )
    return await service.create_source(
        tenant_id=context.tenant_id,
        request=request,
        file_name=file.filename or "upload.txt",
        mime_type=file.content_type,
        file_bytes=file_bytes,
    )


@router.get(
    "/sources",
    response_model=KnowledgeSourceListResponse,
    summary="List knowledge sources (admin)",
)
async def list_knowledge_sources(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[KnowledgeAdminService, Depends(get_knowledge_admin_service)],
    exam_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> KnowledgeSourceListResponse:
    _require_admin(context)
    return await service.list_sources(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/sources/{source_id}",
    response_model=KnowledgeSourceResponse,
    summary="Get knowledge source details (admin)",
)
async def get_knowledge_source(
    source_id: UUID,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[KnowledgeAdminService, Depends(get_knowledge_admin_service)],
) -> KnowledgeSourceResponse:
    _require_admin(context)
    return await service.get_source(tenant_id=context.tenant_id, source_id=source_id)
