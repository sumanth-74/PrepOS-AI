from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_login_me_flow(client: AsyncClient) -> None:
    slug = "institute-alpha"
    register_payload = {
        "tenant_slug": slug,
        "tenant_name": "Institute Alpha",
        "email": "admin@example.com",
        "password": "StrongPass123!",
        "full_name": "Alpha Admin",
    }
    register_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    tokens = register_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_response.status_code == 200
    me = me_response.json()
    assert me["email"] == "admin@example.com"
    assert "institute_admin" in me["roles"]

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": slug,
            "email": "admin@example.com",
            "password": "StrongPass123!",
        },
    )
    assert login_response.status_code == 200

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_response.json()["refresh_token"]},
    )
    assert refresh_response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code == 401
