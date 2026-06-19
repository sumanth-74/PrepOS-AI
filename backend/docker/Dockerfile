FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip hatchling \
    && pip install .

FROM base AS runtime

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY alembic ./alembic
COPY alembic.ini .
COPY src ./src

RUN useradd --create-home --shell /bin/bash prepos
USER prepos

EXPOSE 8000

CMD ["uvicorn", "prepos.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
