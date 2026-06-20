#!/usr/bin/env bash
# Repair local DB migration drift, enable pgvector, and apply pending Alembic revisions.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source .venv/bin/activate

python <<'PY'
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from prepos.core.config import get_settings

async def main() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")
        )
    await engine.dispose()

asyncio.run(main())
print("Ensured alembic_version.version_num supports long revision ids.")
PY

python scripts/ensure_pgvector.py
alembic upgrade head
echo "Database is at: $(alembic current | tail -1)"
