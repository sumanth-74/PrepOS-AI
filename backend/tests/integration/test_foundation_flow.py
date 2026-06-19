from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.infrastructure.db.models.foundation import AuditLogModel, OutboxEventModel, UserModel


@pytest.mark.asyncio
async def test_health_endpoints(client: AsyncClient) -> None:
    health = await client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    ready = await client.get("/health/ready")
    assert ready.status_code == 200
    body = ready.json()
    assert body["status"] == "ok"
    assert body["checks"]["api"] == "ok"
    assert body["checks"]["database"] == "ok"


@pytest.mark.asyncio
async def test_register_emits_student_registered_outbox_and_audit(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_slug": "foundation-outbox-tenant",
            "tenant_name": "Foundation Outbox Institute",
            "email": "outbox@example.com",
            "password": "StrongPass123!",
            "full_name": "Outbox Admin",
        },
    )
    assert response.status_code == 201

    outbox_result = await db_session.execute(
        select(OutboxEventModel).where(OutboxEventModel.event_type == "StudentRegistered")
    )
    outbox_row = outbox_result.scalar_one()
    assert outbox_row.tenant_id is not None
    assert outbox_row.producer == "auth_service"
    assert "user_id" in outbox_row.payload

    audit_result = await db_session.execute(
        select(AuditLogModel).where(AuditLogModel.action == "tenant.registered")
    )
    audit_row = audit_result.scalar_one()
    assert audit_row.tenant_id == outbox_row.tenant_id


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_slug": "foundation-logout-tenant",
            "tenant_name": "Logout Institute",
            "email": "logout@example.com",
            "password": "StrongPass123!",
            "full_name": "Logout Admin",
        },
    )
    assert register.status_code == 201
    refresh_token = register.json()["refresh_token"]
    access_token = register.json()["access_token"]

    logout = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert logout.status_code == 204

    refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh.status_code == 401


@pytest.mark.asyncio
async def test_cross_tenant_email_isolation(client: AsyncClient, db_session: AsyncSession) -> None:
    shared_email = "shared@example.com"
    password = "StrongPass123!"

    tenant_a = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_slug": "tenant-a-isolation",
            "tenant_name": "Tenant A",
            "email": shared_email,
            "password": password,
            "full_name": "Tenant A Admin",
        },
    )
    assert tenant_a.status_code == 201
    token_a = tenant_a.json()["access_token"]

    tenant_b = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_slug": "tenant-b-isolation",
            "tenant_name": "Tenant B",
            "email": shared_email,
            "password": password,
            "full_name": "Tenant B Admin",
        },
    )
    assert tenant_b.status_code == 201
    token_b = tenant_b.json()["access_token"]

    me_a = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    me_b = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    assert me_a.status_code == 200
    assert me_b.status_code == 200
    assert me_a.json()["tenant_id"] != me_b.json()["tenant_id"]
    assert me_a.json()["id"] != me_b.json()["id"]

    users_result = await db_session.execute(select(UserModel).where(UserModel.email == shared_email))
    users = list(users_result.scalars().all())
    assert len(users) == 2
    tenant_ids = {user.tenant_id for user in users}
    assert len(tenant_ids) == 2


@pytest.mark.asyncio
async def test_duplicate_tenant_slug_rejected(client: AsyncClient) -> None:
    payload = {
        "tenant_slug": "duplicate-slug-tenant",
        "tenant_name": "First Institute",
        "email": "first@example.com",
        "password": "StrongPass123!",
        "full_name": "First Admin",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    payload["email"] = "second@example.com"
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
