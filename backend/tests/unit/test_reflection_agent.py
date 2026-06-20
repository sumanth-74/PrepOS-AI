from __future__ import annotations

from uuid import uuid4

from prepos.application.agents.critic_agent import CriticAgent
from prepos.application.agents.models import AgentCritiqueRecord, AgentResult
from prepos.application.agents.reflection_agent import ReflectionAgent


def test_reflection_improves_failed_critique() -> None:
    critic = CriticAgent()
    reflection = ReflectionAgent()
    results = [
        AgentResult(
            success=True,
            confidence="high",
            reasoning="Top recommendation: Federalism.",
            data={"recommendations": [{"concept_name": "Federalism"}]},
            tool_name="recommendation",
        )
    ]
    critique = critic.review(
        execution_id=uuid4(),
        answer="Readiness score is 99% with guaranteed prelims success.",
        results=results,
        sources=[],
    )
    assert critique.passed is False
    record = reflection.reflect(
        execution_id=critique.execution_id,
        critique=critique,
        original_answer="Readiness score is 99% with guaranteed prelims success.",
        results=results,
    )
    assert record is not None
    assert "Federalism" in record.refined_answer


def test_reflection_skips_passed_critique() -> None:
    reflection = ReflectionAgent()
    critique = AgentCritiqueRecord(
        critique_id=uuid4(),
        execution_id=uuid4(),
        overall_score=0.9,
        passed=True,
    )
    assert (
        reflection.reflect(
            execution_id=critique.execution_id,
            critique=critique,
            original_answer="All good.",
            results=[],
        )
        is None
    )
