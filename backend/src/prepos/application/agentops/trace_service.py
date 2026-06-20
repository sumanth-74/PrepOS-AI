from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog

from prepos.application.agentops.evaluation_engine import AgentEvaluationEngine
from prepos.application.agentops.models import (
    AgentCostRecord,
    AgentEvaluationScores,
    AgentTraceArtifactRecord,
    AgentTraceStepRecord,
)
from prepos.application.agentops.ports import AgentOpsRepositoryPort
from prepos.application.agents.models import AgentOrchestratorResponse

logger = structlog.get_logger(__name__)

COST_PER_1K_TOKENS = 0.002


class AgentTraceService:
    """Records full execution traces for AgentOps observability."""

    def __init__(
        self,
        *,
        repository: AgentOpsRepositoryPort,
        evaluation_engine: AgentEvaluationEngine | None = None,
    ) -> None:
        self._repository = repository
        self._evaluation_engine = evaluation_engine or AgentEvaluationEngine()

    async def record_execution(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        question: str,
        latency_ms: int,
        response: AgentOrchestratorResponse,
    ) -> UUID:
        now = datetime.now(UTC)
        steps: list[AgentTraceStepRecord] = []
        step_number = 1
        steps.append(
            AgentTraceStepRecord(
                step_number=step_number,
                agent_name="planner_agent",
                tool_name=None,
                input_json={"question": question, "persona": persona},
                output_json=response.plan.model_dump(mode="json"),
                latency_ms=0,
                status="completed",
            )
        )
        if response.execution_graph:
            for node in response.execution_graph.nodes:
                step_number += 1
                steps.append(
                    AgentTraceStepRecord(
                        step_number=step_number,
                        agent_name=node.agent_type,
                        tool_name=node.tool_name,
                        input_json={"objective": question},
                        output_json=node.result.model_dump(mode="json") if node.result else {},
                        latency_ms=0,
                        status=node.status,
                    )
                )
        if response.critique:
            step_number += 1
            steps.append(
                AgentTraceStepRecord(
                    step_number=step_number,
                    agent_name="critic_agent",
                    input_json={"answer": response.answer},
                    output_json=response.critique.model_dump(mode="json"),
                    status="completed" if response.critique.passed else "flagged",
                )
            )
        if response.reflection:
            step_number += 1
            steps.append(
                AgentTraceStepRecord(
                    step_number=step_number,
                    agent_name="reflection_agent",
                    input_json={"original_answer": response.reflection.original_answer},
                    output_json=response.reflection.model_dump(mode="json"),
                    status="completed",
                )
            )

        artifacts = [
            AgentTraceArtifactRecord(artifact_type="plan", artifact_json=response.plan.model_dump(mode="json")),
        ]
        if response.critique:
            artifacts.append(
                AgentTraceArtifactRecord(
                    artifact_type="critique",
                    artifact_json=response.critique.model_dump(mode="json"),
                )
            )
        if response.reflection:
            artifacts.append(
                AgentTraceArtifactRecord(
                    artifact_type="reflection",
                    artifact_json=response.reflection.model_dump(mode="json"),
                )
            )
        if response.execution_graph:
            artifacts.append(
                AgentTraceArtifactRecord(
                    artifact_type="execution_graph",
                    artifact_json=response.execution_graph.model_dump(mode="json"),
                )
            )

        trace_id = await self._repository.save_trace(
            tenant_id=tenant_id,
            execution_id=response.execution_id or uuid4(),
            user_id=user_id,
            persona=persona,
            question=question,
            answer=response.answer,
            confidence=response.confidence,
            latency_ms=latency_ms,
            steps=steps,
            artifacts=artifacts,
            now=now,
        )

        scores = self._evaluation_engine.evaluate(response=response, trace_id=trace_id)
        await self._repository.save_evaluation(tenant_id=tenant_id, scores=scores, now=now)

        tokens_in = max(1, len(question.split()))
        tokens_out = max(1, len(response.answer.split()))
        for agent_type in response.collaborating_agents or [response.agent_used]:
            await self._repository.save_cost(
                tenant_id=tenant_id,
                record=AgentCostRecord(
                    agent_type=agent_type,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    estimated_cost=round((tokens_in + tokens_out) / 1000 * COST_PER_1K_TOKENS, 6),
                    latency_ms=latency_ms,
                ),
                trace_id=trace_id,
                execution_id=response.execution_id,
                now=now,
            )

        logger.info(
            "agent_trace_recorded",
            tenant_id=str(tenant_id),
            trace_id=str(trace_id),
            step_count=len(steps),
        )
        return trace_id

    async def list_traces(self, *, tenant_id: UUID, limit: int = 50, offset: int = 0):
        return await self._repository.list_traces(tenant_id=tenant_id, limit=limit, offset=offset)

    async def get_trace(self, *, tenant_id: UUID, trace_id: UUID):
        return await self._repository.get_trace(tenant_id=tenant_id, trace_id=trace_id)

    async def export_trace(self, *, tenant_id: UUID, trace_id: UUID):
        return await self._repository.export_trace(tenant_id=tenant_id, trace_id=trace_id)
