from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.exam.seed_catalog import CATALOG_VERSION, EXAM_ID
from prepos.application.exam.services import SeedLoaderService
from prepos.application.exam.use_cases import (
    GetConceptAncestorsUseCase,
    GetExamTreeUseCase,
    PublishCatalogVersionUseCase,
    SearchConceptsUseCase,
)
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork


async def _register_super_admin(client: AsyncClient, db_session: AsyncSession) -> str:
    from sqlalchemy import select

    from prepos.infrastructure.db.models.foundation import RoleModel, UserRoleModel

    tenant_slug = "exam-test-tenant"
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "Exam Test Institute",
            "tenant_slug": tenant_slug,
            "email": "admin@example.com",
            "password": "SecurePass123!",
            "full_name": "Exam Admin",
        },
    )
    assert register_response.status_code == 201
    access_token = register_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    me = me_response.json()

    role_result = await db_session.execute(select(RoleModel).where(RoleModel.name == "super_admin"))
    role = role_result.scalar_one()
    db_session.add(
        UserRoleModel(
            tenant_id=me["tenant_id"],
            user_id=me["id"],
            role_id=role.id,
        )
    )
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": tenant_slug,
            "email": "admin@example.com",
            "password": "SecurePass123!",
        },
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_exam_catalog_seed_publish_and_query(client: AsyncClient, db_session: AsyncSession) -> None:
    token = await _register_super_admin(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}

    import_response = await client.post("/api/v1/syllabus/seed/import", headers=headers)
    assert import_response.status_code == 200
    body = import_response.json()
    assert body["exam_id"] == EXAM_ID
    assert body["concepts_imported"] >= 497

    publish_response = await client.post(
        f"/api/v1/syllabus/{EXAM_ID}/catalog/versions/{CATALOG_VERSION}/publish",
        headers=headers,
        json={"change_summary": "Initial publish"},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"

    tree_response = await client.get(f"/api/v1/syllabus/{EXAM_ID}/tree", headers=headers)
    assert tree_response.status_code == 200
    tree = tree_response.json()
    assert tree["exam"]["exam_id"] == EXAM_ID
    assert len(tree["subjects"]) >= 17

    search_response = await client.get(
        "/api/v1/concepts/search",
        params={"exam_id": EXAM_ID, "query": "Article 14"},
        headers=headers,
    )
    assert search_response.status_code == 200
    search = search_response.json()
    assert search["total"] >= 1

    concept_id = search["items"][0]["concept_id"]
    ancestors_response = await client.get(f"/api/v1/concepts/{concept_id}/ancestors", headers=headers)
    assert ancestors_response.status_code == 200
    ancestors = ancestors_response.json()
    assert ancestors["concept"]["concept_id"] == concept_id
    assert ancestors["topic"]["topic_id"] is not None


@pytest.mark.asyncio
async def test_domain_catalog_updated_outbox_event(db_session: AsyncSession) -> None:
    uow = SqlAlchemyExamCatalogUnitOfWork(db_session)
    loader = SeedLoaderService(uow)
    await loader.import_default_seed()
    await uow.commit()

    from uuid import uuid4

    from prepos.core.tenancy import RoleName, TenantContext

    outbox = OutboxPublisher(db_session)
    publish = PublishCatalogVersionUseCase(uow, outbox)
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=frozenset({RoleName.SUPER_ADMIN}),
        correlation_id="test-correlation",
    )
    await publish.execute(context=context, exam_id=EXAM_ID, version=CATALOG_VERSION)
    await uow.commit()

    from sqlalchemy import select

    from prepos.infrastructure.db.models.foundation import OutboxEventModel

    result = await db_session.execute(
        select(OutboxEventModel).where(OutboxEventModel.event_type == "DomainCatalogUpdated")
    )
    row = result.scalar_one()
    assert row.tenant_id is None
    assert row.payload["exam_id"] == EXAM_ID
    assert row.metadata_json is not None
    assert row.metadata_json.get("scope") == "platform"


@pytest.mark.asyncio
async def test_catalog_is_platform_global_not_tenant_scoped(db_session: AsyncSession) -> None:
    uow = SqlAlchemyExamCatalogUnitOfWork(db_session)
    loader = SeedLoaderService(uow)
    await loader.import_default_seed()
    await uow.commit()

    tree = await GetExamTreeUseCase(uow).execute(EXAM_ID)
    assert len(tree.subjects) >= 17

    search = await SearchConceptsUseCase(uow).execute(exam_id=EXAM_ID, query="Parliament", limit=5)
    assert search.total >= 1

    concept_id = "upsc_cse.polity.fundamental_rights.article_14"
    ancestors = await GetConceptAncestorsUseCase(uow).execute(concept_id)
    assert ancestors.concept.concept_id == concept_id
    assert any(item.concept_slug == "overview" for item in ancestors.ancestors)
