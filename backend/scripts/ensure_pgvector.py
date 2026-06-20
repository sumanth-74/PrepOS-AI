#!/usr/bin/env python3
"""Ensure the pgvector extension exists before Alembic migration 028."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

_SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prepos.core.config import get_settings  # noqa: E402


def _is_privilege_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return "permission denied" in message or "insufficientprivilege" in message


def _postgres_superuser_url(database_url: str) -> str:
    parsed = urlparse(database_url.replace("postgresql+asyncpg://", "postgresql://", 1))
    explicit_superuser = os.environ.get("POSTGRES_SUPERUSER")
    superuser = explicit_superuser or parsed.username or "postgres"
    password = os.environ.get("POSTGRES_SUPERUSER_PASSWORD")
    if password is None and parsed.password and explicit_superuser is None:
        password = parsed.password
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    database = parsed.path.lstrip("/") or "prepos"

    if password:
        auth = f"{superuser}:{password}"
    else:
        auth = superuser

    return f"postgresql+asyncpg://{auth}@{host}:{port}/{database}"


async def _extension_exists(engine_url: str) -> bool:
    engine = create_async_engine(engine_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            return result.scalar() is not None
    finally:
        await engine.dispose()


async def _create_extension(engine_url: str) -> None:
    engine = create_async_engine(engine_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    finally:
        await engine.dispose()


def _create_extension_via_psql(database_name: str) -> bool:
    try:
        subprocess.run(
            ["psql", "-d", database_name, "-c", "CREATE EXTENSION IF NOT EXISTS vector;"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


async def ensure_pgvector() -> None:
    settings = get_settings()
    app_url = settings.database_url

    if await _extension_exists(app_url):
        print("pgvector extension already enabled.")
        return

    candidates = [app_url]
    superuser_url = os.environ.get("DATABASE_SUPERUSER_URL")
    if superuser_url:
        candidates.append(superuser_url)
    candidates.append(_postgres_superuser_url(app_url))

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            await _create_extension(candidate)
            if await _extension_exists(app_url):
                print("pgvector extension enabled.")
                return
        except Exception as exc:
            last_error = exc
            if not _is_privilege_error(exc):
                raise

    database_name = urlparse(
        app_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    ).path.lstrip("/") or "prepos"
    if _create_extension_via_psql(database_name) and await _extension_exists(app_url):
        print("pgvector extension enabled via local psql superuser.")
        return

    message = (
        "Could not enable pgvector. The app database user lacks superuser privileges.\n"
        "Run once as a Postgres superuser:\n"
        '  psql -U postgres -d prepos -c "CREATE EXTENSION IF NOT EXISTS vector;"\n'
        "Or set DATABASE_SUPERUSER_URL / POSTGRES_SUPERUSER_PASSWORD and rerun migrate-db.sh."
    )
    if last_error is not None:
        raise RuntimeError(message) from last_error
    raise RuntimeError(message)


def main() -> None:
    asyncio.run(ensure_pgvector())


if __name__ == "__main__":
    main()
