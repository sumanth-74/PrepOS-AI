from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from prepos.application.agentops.models import AgentEvaluationScores
from prepos.application.agents.models import AgentOrchestratorResponse


class AgentEvaluationEngine:
    """Deterministic evaluation of planner, retrieval, reflection, and agent quality."""

    def evaluate(self, *, response: AgentOrchestratorResponse, trace_id: UUID) -> AgentEvaluationScores:
        tool_results = response.results
        successful_tools = sum(1 for item in tool_results if item.success)
        total_tools = max(len(tool_results), 1)
        support_score = round(successful_tools / total_tools, 4)

        citation_score = 1.0 if response.sources else 0.0
        if response.critique and response.critique.citation_issues:
            citation_score = max(0.0, citation_score - 0.5)

        hallucination_score = 0.0
        if response.critique:
            hallucination_score = round(
                len(response.critique.unsupported_claims) * 0.25 + len(response.critique.citation_issues) * 0.15,
                4,
            )
            hallucination_score = min(1.0, hallucination_score)

        retrieval_score = support_score
        if any(item.tool_name == "knowledge" for item in tool_results):
            knowledge = next(item for item in tool_results if item.tool_name == "knowledge")
            retrieval_score = 1.0 if knowledge.success and knowledge.sources else 0.5

        planner_steps = len(response.plan.steps)
        expected_min = 1
        unnecessary = max(0, planner_steps - 8)
        missing = 0 if successful_tools else 1
        planner_quality_score = round(max(0.0, 1.0 - unnecessary * 0.05 - missing * 0.3), 4)

        answer_quality_score = response.critique.overall_score if response.critique else support_score
        if response.reflection:
            answer_quality_score = round(min(1.0, answer_quality_score + 0.1), 4)

        return AgentEvaluationScores(
            evaluation_id=uuid4(),
            trace_id=trace_id,
            execution_id=response.execution_id or uuid4(),
            retrieval_score=retrieval_score,
            citation_score=citation_score,
            hallucination_score=hallucination_score,
            support_score=support_score,
            answer_quality_score=answer_quality_score,
            planner_quality_score=planner_quality_score,
            details={
                "planner_steps": planner_steps,
                "successful_tools": successful_tools,
                "critique_passed": response.critique.passed if response.critique else None,
                "reflection_applied": response.reflection is not None,
            },
            created_at=datetime.now(UTC),
        )
