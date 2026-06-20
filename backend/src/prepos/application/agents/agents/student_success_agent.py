from __future__ import annotations

import structlog

from prepos.application.agents.base_agent import BaseAgent
from prepos.application.agents.models import AgentContext, AgentResult, AgentSource
from prepos.application.agents.registry import ToolRegistry

logger = structlog.get_logger(__name__)


class CompositeAgent(BaseAgent):
    def __init__(self, *, agent_type: str, default_tools: list[str], registry: ToolRegistry) -> None:
        self.agent_type = agent_type
        self._default_tools = default_tools
        self._registry = registry

    async def run(
        self,
        *,
        context: AgentContext,
        objective: str,
        tool_names: list[str] | None = None,
    ) -> AgentResult:
        selected = tool_names or self._default_tools
        child_results: list[AgentResult] = []
        sources: list[AgentSource] = []

        for tool_name in selected:
            tool = self._registry.get(tool_name)
            if tool is None:
                continue
            logger.info(
                "agent_tool_invoked",
                agent_type=self.agent_type,
                tool_name=tool_name,
                tenant_id=str(context.tenant_id),
            )
            result = await tool.execute(context=context)
            result.agent_type = self.agent_type
            result.tool_name = tool_name
            child_results.append(result)
            sources.extend(result.sources)

        if not child_results:
            return AgentResult(
                success=False,
                confidence="low",
                reasoning="No tools could be executed for this agent.",
                agent_type=self.agent_type,
            )

        successful = [item for item in child_results if item.success]
        confidence = "high" if len(successful) >= max(1, len(child_results) // 2) else "medium"
        if not successful:
            confidence = "low"

        summary_lines = [self._summarize_result(item) for item in child_results if item.success]
        answer = "\n".join(summary_lines) if summary_lines else "Unable to gather agent context."

        return AgentResult(
            success=bool(successful),
            confidence=confidence,
            data={"tool_results": [item.model_dump(mode="json") for item in child_results]},
            reasoning=f"{self.agent_type} synthesized {len(successful)}/{len(child_results)} tool results.",
            sources=sources,
            agent_type=self.agent_type,
        )

    @staticmethod
    def _summarize_result(result: AgentResult) -> str:
        tool = result.tool_name or "tool"
        if tool == "forecasting":
            probability = result.data.get("probability_of_success") or result.data.get("average_probability")
            if probability is not None:
                return f"Forecast: success probability {probability}%."
        if tool == "recommendation":
            recommendations = result.data.get("recommendations") or []
            if recommendations:
                top = recommendations[0]
                return f"Top recommendation: {top.get('concept_name', top.get('concept_id', 'concept'))}."
        if tool == "planning":
            return "Adaptive study plan loaded."
        if tool == "memory":
            lines = result.data.get("context_lines") or []
            if lines:
                return f"Memory context: {lines[0]}"
        if tool == "twin":
            readiness = result.data.get("dashboard", {}).get("readiness_score")
            if readiness is not None:
                return f"Current readiness: {readiness}."
        if tool == "institution":
            health = result.data.get("dashboard", {}).get("kpis", {}).get("institution_health_score")
            if health is not None:
                return f"Institution health score: {health}/100."
        if tool == "intervention":
            recs = result.data.get("recommended_interventions") or []
            if recs:
                return f"Top intervention: {recs[0].get('intervention_type', 'intervention')}."
        return result.reasoning or f"{tool} completed successfully."


class StudentSuccessAgent(CompositeAgent):
    def __init__(self, registry: ToolRegistry) -> None:
        super().__init__(
            agent_type="student_success_agent",
            default_tools=["memory", "forecasting", "recommendation", "planning", "twin", "pyq", "current_affairs"],
            registry=registry,
        )


class MentorCoachAgent(CompositeAgent):
    def __init__(self, registry: ToolRegistry) -> None:
        super().__init__(
            agent_type="mentor_coach_agent",
            default_tools=["memory", "forecasting", "intervention", "recommendation", "planning", "twin", "pyq"],
            registry=registry,
        )


class InstitutionStrategyAgent(CompositeAgent):
    def __init__(self, registry: ToolRegistry) -> None:
        super().__init__(
            agent_type="institution_strategy_agent",
            default_tools=["institution", "cohort", "forecasting", "intervention"],
            registry=registry,
        )
