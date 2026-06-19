#!/usr/bin/env python3
"""S0/S1 dev smoke test: foundation, auth, tenancy, outbox."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://127.0.0.1:8000")


def _env() -> dict[str, str]:
    return {
        **os.environ,
        "DATABASE_URL": os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://prepos:prepos@localhost:5432/prepos",
        ),
        "SECRET_KEY": os.environ.get(
            "SECRET_KEY",
            "dev-smoke-test-secret-key-minimum-32-characters-long",
        ),
        "CORS_ORIGINS": os.environ.get("CORS_ORIGINS", '["http://localhost:3000"]'),
        "CELERY_TASK_ALWAYS_EAGER": "true",
    }


def run_migrations() -> None:
    print("==> alembic upgrade head")
    subprocess.run(
        [str(BACKEND_ROOT / ".venv/bin/alembic"), "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=_env(),
        check=True,
    )


async def run_smoke() -> None:
    slug = "s0-s1-smoke-tenant"
    email = "s0s1-smoke@example.com"
    password = "SecurePass123!"

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        health = await client.get("/health")
        print(f"==> GET /health -> {health.status_code}")
        health.raise_for_status()

        ready = await client.get("/health/ready")
        print(f"==> GET /health/ready -> {ready.status_code}")
        ready.raise_for_status()
        ready_body = ready.json()
        print(json.dumps(ready_body, indent=2))
        assert ready_body["status"] == "ok"
        assert ready_body["checks"]["database"] == "ok"

        openapi = await client.get("/openapi.json")
        print(f"==> GET /openapi.json -> {openapi.status_code}")
        openapi.raise_for_status()
        paths = openapi.json()["paths"]
        for required in (
            "/health",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/auth/logout",
            "/api/v1/auth/me",
        ):
            assert required in paths, f"missing OpenAPI path: {required}"

        unauthorized = await client.get("/api/v1/auth/me")
        print(f"==> GET /auth/me without token -> {unauthorized.status_code}")
        assert unauthorized.status_code == 401

        register = await client.post(
            "/api/v1/auth/register",
            json={
                "tenant_slug": slug,
                "tenant_name": "S0 S1 Smoke Institute",
                "email": email,
                "password": password,
                "full_name": "Smoke Admin",
            },
        )
        print(f"==> POST /auth/register -> {register.status_code}")
        if register.status_code not in {201, 409}:
            register.raise_for_status()

        login = await client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": slug, "email": email, "password": password},
        )
        print(f"==> POST /auth/login -> {login.status_code}")
        login.raise_for_status()
        tokens = login.json()

        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        print(f"==> GET /auth/me -> {me.status_code}")
        me.raise_for_status()
        me_body = me.json()
        print(json.dumps({"email": me_body["email"], "roles": me_body["roles"]}, indent=2))
        assert me_body["email"] == email
        assert "institute_admin" in me_body["roles"]

        refresh = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        print(f"==> POST /auth/refresh -> {refresh.status_code}")
        refresh.raise_for_status()

        logout = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {refresh.json()['access_token']}"},
            json={"refresh_token": refresh.json()["refresh_token"]},
        )
        print(f"==> POST /auth/logout -> {logout.status_code}")
        assert logout.status_code == 204

        revoked = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh.json()["refresh_token"]},
        )
        print(f"==> POST /auth/refresh after logout -> {revoked.status_code}")
        assert revoked.status_code == 401

    print("S0/S1 smoke test PASSED")


def main() -> int:
    if os.environ.get("SMOKE_SKIP_MIGRATE") != "1":
        run_migrations()
    try:
        asyncio.run(run_smoke())
    except httpx.ConnectError:
        print(
            "API not reachable. Start server first:\n"
            "  cd backend && uvicorn prepos.api.main:app --reload --port 8000",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
