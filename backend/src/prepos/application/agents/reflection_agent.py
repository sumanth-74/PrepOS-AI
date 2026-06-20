from __future__ import annotations

from uuid import uuid4

import structlog

from prepos.application.agents.models import AgentCritiqueRecord, AgentReflectionRecord, AgentResult

logger = structlog.get_logger(__name__)


class ReflectionAgent:
    """Improves weak responses using critique feedback and successful tool outputs."""

    agent_type = "reflection_agent"

    def reflect(
        self,
        *,
        execution_id,
        critique: AgentCritiqueRecord,
        original_answer: str,
        results: list[AgentResult],
    ) -> AgentReflectionRecord | None:
        if critique.passed:
            return None

        improvements: list[str] = []
        refined_lines: list[str] = []

        if critique.unsupported_claims:
            improvements.append("Removed unsupported numeric claims not backed by tool evidence.")
        if critique.citation_issues:
            improvements.append("Added explicit citations from successful tool outputs.")

        refined_lines.append("Based on verified agent tool outputs:")
        for result in results:
            if result.success and result.reasoning:
                refined_lines.append(f"- {result.reasoning}")
                for source in result.sources:
                    refined_lines.append(f"  Source: {source.label} ({source.reference})")

        if not any(item.success for item in results):
            refined_lines.append(
                "I could not verify enough evidence to answer confidently. "
                "Please retry with a narrower question or ensure student context is available."
            )
            improvements.append("Replaced weak synthesis with evidence-limited response.")

        refined_answer = "\n".join(refined_lines).strip()
        logger.info(
            "agent_reflection_completed",
            execution_id=str(execution_id),
            improvement_count=len(improvements),
        )
        return AgentReflectionRecord(
            reflection_id=uuid4(),
            execution_id=execution_id,
            critique_id=critique.critique_id,
            original_answer=original_answer,
            refined_answer=refined_answer,
            improvements=improvements,
        )
