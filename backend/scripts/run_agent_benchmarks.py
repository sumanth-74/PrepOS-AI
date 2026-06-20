#!/usr/bin/env python3
"""Continuous agent benchmarking entrypoint for CI/CD (P10 S44)."""

from __future__ import annotations

import sys

from prepos.application.agentops.evaluation_service import AgentEvaluationService
from prepos.application.agentops.models import AgentBenchmarkRunRequest
from prepos.application.agentops.ports import AgentOpsRepositoryPort


class _InMemoryBenchmarkRepo(AgentOpsRepositoryPort):
    async def save_benchmark(self, *, record):
        self.last_record = record
        return record.benchmark_id

    async def list_benchmarks(self, *, tenant_id, limit):
        return []

    async def save_trace(self, **kwargs):
        raise NotImplementedError

    async def list_traces(self, **kwargs):
        raise NotImplementedError

    async def get_trace(self, **kwargs):
        raise NotImplementedError

    async def export_trace(self, **kwargs):
        raise NotImplementedError

    async def save_evaluation(self, **kwargs):
        raise NotImplementedError

    async def get_evaluation_dashboard(self, **kwargs):
        raise NotImplementedError

    async def save_feedback(self, **kwargs):
        raise NotImplementedError

    async def get_feedback_analytics(self, **kwargs):
        raise NotImplementedError

    async def save_cost(self, **kwargs):
        raise NotImplementedError

    async def get_cost_dashboard(self, **kwargs):
        raise NotImplementedError

    async def create_pending_action(self, **kwargs):
        raise NotImplementedError

    async def list_pending_actions(self, **kwargs):
        raise NotImplementedError

    async def update_pending_action_status(self, **kwargs):
        raise NotImplementedError

    async def list_experiments(self, **kwargs):
        raise NotImplementedError

    async def list_prompts(self, **kwargs):
        raise NotImplementedError

    async def get_agent_health_details(self, **kwargs):
        raise NotImplementedError


async def _run() -> int:
    repo = _InMemoryBenchmarkRepo()
    service = AgentEvaluationService(repository=repo)
    suites = ["planner", "reflection", "workflow"]
    for suite in suites:
        record = await service.run_benchmark(tenant_id=None, request=AgentBenchmarkRunRequest(suite_type=suite))
        if record.failed_count > 0:
            print(f"Benchmark regression in suite {suite}: {record.failed_count} failures")
            return 1
        print(f"Benchmark suite {suite}: {record.passed_count}/{record.scenario_count} passed")
    return 0


def main() -> None:
    import asyncio

    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
