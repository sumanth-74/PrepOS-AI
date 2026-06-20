from __future__ import annotations

import structlog

from prepos.application.agents.agent_marketplace import AgentMarketplace
from prepos.application.agents.models import (
    AgentContext,
    AgentExecutionGraph,
    AgentExecutionGraphNode,
    AgentExecutionPlan,
    AgentResult,
)
from prepos.application.agents.synthesis import synthesize_collaborative_answer

logger = structlog.get_logger(__name__)


class CollaborationExecutor:
    """Executes multi-agent plans and builds an auditable execution graph."""

    def __init__(self, *, marketplace: AgentMarketplace) -> None:
        self._marketplace = marketplace

    async def execute_plan(
        self,
        *,
        context: AgentContext,
        plan: AgentExecutionPlan,
        coordinator_agent: str,
    ) -> tuple[AgentResult, AgentExecutionGraph, list[str]]:
        graph_nodes: list[AgentExecutionGraphNode] = []
        child_results: list[AgentResult] = []
        collaborating_agents: list[str] = []
        parent_node_id: str | None = None

        for step in sorted(plan.steps, key=lambda item: item.step_order):
            agent = self._marketplace.get(step.agent_type)
            if agent is None:
                continue
            if step.agent_type not in collaborating_agents:
                collaborating_agents.append(step.agent_type)

            logger.info(
                "agent_collaboration_step_started",
                agent_type=step.agent_type,
                tenant_id=str(context.tenant_id),
                step_order=step.step_order,
            )
            step_result = await agent.run(
                context=context,
                objective=step.objective,
                tool_names=step.tool_names,
            )
            if step_result.data.get("tool_results"):
                for payload in step_result.data["tool_results"]:
                    validated = AgentResult.model_validate(payload)
                    validated.agent_type = step.agent_type
                    child_results.append(validated)
            else:
                step_result.agent_type = step.agent_type
                child_results.append(step_result)

            node_id = f"{step.agent_type}_{step.step_order}"
            graph_nodes.append(
                AgentExecutionGraphNode(
                    node_id=node_id,
                    parent_node_id=parent_node_id,
                    agent_type=step.agent_type,
                    tool_name=step.tool_names[0] if step.tool_names else None,
                    step_order=step.step_order,
                    status="completed" if step_result.success else "failed",
                    result=step_result,
                )
            )
            parent_node_id = node_id
            context.shared_state[step.agent_type] = step_result.model_dump(mode="json")

        confidence, answer, sources = synthesize_collaborative_answer(
            coordinator_agent=coordinator_agent,
            results=child_results,
        )
        aggregate = AgentResult(
            success=any(item.success for item in child_results),
            confidence=confidence,
            data={"tool_results": [item.model_dump(mode="json") for item in child_results]},
            reasoning=answer,
            sources=sources,
            agent_type=coordinator_agent,
        )
        graph = AgentExecutionGraph(nodes=graph_nodes)
        return aggregate, graph, collaborating_agents
