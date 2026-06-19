#!/usr/bin/env python3
"""S2 dev smoke test: migrate → seed → publish → query."""

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
EXAM_ID = "upsc_cse"
CATALOG_VERSION = "1.0.0"


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


async def _super_admin_token(client: httpx.AsyncClient) -> str:
    tenant_slug = "s2-smoke-tenant"
    email = "smoke-admin@example.com"
    password = "SecurePass123!"

    register = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "S2 Smoke Institute",
            "tenant_slug": tenant_slug,
            "email": email,
            "password": password,
            "full_name": "Smoke Admin",
        },
    )
    if register.status_code not in {201, 409}:
        raise RuntimeError(f"register failed: {register.status_code} {register.text}")

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from prepos.infrastructure.db.models.foundation import RoleModel, UserModel, UserRoleModel

    engine = create_async_engine(_env()["DATABASE_URL"])
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        user_result = await session.execute(select(UserModel).where(UserModel.email == email))
        user = user_result.scalar_one()
        role_result = await session.execute(select(RoleModel).where(RoleModel.name == "super_admin"))
        role = role_result.scalar_one()
        existing = await session.execute(
            select(UserRoleModel).where(
                UserRoleModel.user_id == user.id,
                UserRoleModel.role_id == role.id,
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(
                UserRoleModel(
                    tenant_id=user.tenant_id,
                    user_id=user.id,
                    role_id=role.id,
                )
            )
            await session.commit()
    await engine.dispose()

    login = await client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": tenant_slug, "email": email, "password": password},
    )
    if login.status_code != 200:
        raise RuntimeError(f"login failed: {login.status_code} {login.text}")
    return login.json()["access_token"]


async def run_api_smoke() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        health = await client.get("/health")
        print(f"==> GET /health -> {health.status_code}")
        health.raise_for_status()

        token = await _super_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        seed = await client.post("/api/v1/syllabus/seed/import", headers=headers)
        print(f"==> POST /api/v1/syllabus/seed/import -> {seed.status_code}")
        seed.raise_for_status()
        seed_body = seed.json()
        print(json.dumps(seed_body, indent=2))
        assert seed_body["concepts_imported"] >= 497

        publish = await client.post(
            f"/api/v1/syllabus/{EXAM_ID}/catalog/versions/{CATALOG_VERSION}/publish",
            headers=headers,
            json={"change_summary": "S2 dev smoke test publish"},
        )
        print(f"==> POST publish -> {publish.status_code}")
        publish.raise_for_status()
        print(json.dumps(publish.json(), indent=2))

        tree = await client.get(f"/api/v1/syllabus/{EXAM_ID}/tree", headers=headers)
        print(f"==> GET tree -> {tree.status_code}")
        tree.raise_for_status()
        tree_body = tree.json()
        print(
            f"subjects={len(tree_body['subjects'])} "
            f"tracks={len(tree_body['tracks'])} "
            f"catalog={tree_body['catalog_version']}"
        )

        search = await client.get(
            "/api/v1/concepts/search",
            params={"exam_id": EXAM_ID, "query": "Article 14", "limit": 5},
            headers=headers,
        )
        print(f"==> GET concepts/search -> {search.status_code}")
        search.raise_for_status()
        search_body = search.json()
        print(f"search_total={search_body['total']}")

        concept_id = search_body["items"][0]["concept_id"]
        ancestors = await client.get(f"/api/v1/concepts/{concept_id}/ancestors", headers=headers)
        print(f"==> GET ancestors -> {ancestors.status_code}")
        ancestors.raise_for_status()

        print("S2 smoke test PASSED")


def main() -> int:
    if os.environ.get("SMOKE_SKIP_MIGRATE") != "1":
        run_migrations()
    try:
        asyncio.run(run_api_smoke())
    except httpx.ConnectError:
        print(
            "API not reachable. Start server first:\n"
            "  cd backend && DATABASE_URL=... SECRET_KEY=... "
            "uvicorn prepos.api.main:app --reload",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
