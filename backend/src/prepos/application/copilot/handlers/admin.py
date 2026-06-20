from __future__ import annotations

from typing import Any

from prepos.application.copilot.dto import CopilotSourceResponse


def _source(label: str, reference: str) -> CopilotSourceResponse:
    return CopilotSourceResponse(label=label, reference=reference)


async def handle_platform_health(platform: dict[str, Any]) -> tuple[str, list[CopilotSourceResponse]]:
    checks = platform.get("checks", {})
    lines = [
        f"Platform status: {platform.get('status', 'unknown')}.",
        f"- API: {checks.get('api', 'unknown')}.",
        f"- Database: {checks.get('database', 'unknown')}.",
        f"- Redis: {checks.get('redis', 'unknown')}.",
    ]

    worker = platform.get("worker", {})
    lines.append(
        f"- Celery workers: {worker.get('status', 'unknown')} "
        f"({worker.get('worker_count', 0)} worker(s))."
    )

    outbox = platform.get("outbox", {})
    lines.append(
        f"- Outbox: pending {outbox.get('pending', 0)}, failed {outbox.get('failed', 0)}, "
        f"published {outbox.get('published', 0)}."
    )

    return "\n".join(lines), [
        _source("Ops health", "GET /health/ops"),
        _source("Readiness", "GET /health/ready"),
    ]


async def handle_worker_status(worker: dict[str, Any]) -> tuple[str, list[CopilotSourceResponse]]:
    status = worker.get("status", "unknown")
    count = worker.get("worker_count", 0)
    workers = worker.get("workers", [])

    lines = [
        f"Worker status: {status}.",
        f"- Active workers: {count}.",
    ]
    if workers:
        lines.append("- Worker nodes:")
        for name in workers:
            lines.append(f"  • {name}")
    elif status != "ok":
        detail = worker.get("detail")
        if detail:
            lines.append(f"- Detail: {detail}")
        lines.append("- No Celery workers responded to ping.")

    return "\n".join(lines), [_source("Worker health", "GET /health/worker")]


async def handle_outbox_status(outbox: dict[str, Any]) -> tuple[str, list[CopilotSourceResponse]]:
    counts = outbox.get("counts", {})
    lines = [
        f"Outbox status: {outbox.get('status', 'unknown')}.",
        f"- Pending: {counts.get('pending', 0)}.",
        f"- Published: {counts.get('published', 0)}.",
        f"- Failed: {counts.get('failed', 0)}.",
        f"- Total: {counts.get('total', 0)}.",
    ]
    if counts.get("failed", 0) > 0:
        lines.append("- Action: investigate failed outbox events before scaling traffic.")
    if counts.get("pending", 0) > 100:
        lines.append("- Action: outbox backlog is above the degraded threshold.")

    return "\n".join(lines), [_source("Outbox health", "GET /health/outbox")]


async def handle_deployment_readiness(readiness: dict[str, Any]) -> tuple[str, list[CopilotSourceResponse]]:
    ready = readiness.get("ready", False)
    blockers = readiness.get("blockers", [])

    lines = [
        f"Deployment readiness: {'READY' if ready else 'NOT READY'}.",
    ]
    if blockers:
        lines.append("Blockers:")
        for index, blocker in enumerate(blockers, start=1):
            lines.append(f"{index}. {blocker}")
    else:
        lines.append("All core dependencies (API, database, Redis, workers, outbox) are within thresholds.")

    platform = readiness.get("platform", {})
    checks = platform.get("checks", {})
    lines.extend(
        [
            "",
            "Component snapshot:",
            f"- Database: {checks.get('database', 'unknown')}.",
            f"- Redis: {checks.get('redis', 'unknown')}.",
            f"- Workers: {platform.get('worker', {}).get('status', 'unknown')}.",
        ]
    )

    return "\n".join(lines), [
        _source("Ops health", "GET /health/ops"),
        _source("Worker health", "GET /health/worker"),
        _source("Outbox health", "GET /health/outbox"),
    ]
