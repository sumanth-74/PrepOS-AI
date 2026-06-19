#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"

if [[ ! -d .venv ]]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi

source .venv/bin/activate

if ! python -c "import prepos, structlog" >/dev/null 2>&1; then
  echo "Installing backend dependencies..."
  pip install -e ".[dev]"
fi

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Copying .env from .env.example..."
  cp "$ROOT/.env.example" "$ROOT/.env"
fi

echo "Running database migrations..."
bash scripts/migrate-db.sh

PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"

echo "Starting API at http://${HOST}:${PORT}/docs"
exec uvicorn prepos.api.main:app --reload --host "$HOST" --port "$PORT"
