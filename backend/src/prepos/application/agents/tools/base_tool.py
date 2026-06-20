from __future__ import annotations

from prepos.application.agents.models import AgentContext, AgentResult, AgentSource


class BaseTool:
    name: str = "base_tool"

    async def execute(self, *, context: AgentContext) -> AgentResult:
        raise NotImplementedError

    @staticmethod
    def _success(
        *,
        data: dict,
        reasoning: str,
        reference: str,
        label: str,
        confidence: str = "high",
    ) -> AgentResult:
        return AgentResult(
            success=True,
            confidence=confidence,
            data=data,
            reasoning=reasoning,
            sources=[AgentSource(label=label, reference=reference)],
            tool_name=label,
        )

    @staticmethod
    def _failure(*, reasoning: str, tool_name: str) -> AgentResult:
        return AgentResult(
            success=False,
            confidence="low",
            data={},
            reasoning=reasoning,
            tool_name=tool_name,
        )
