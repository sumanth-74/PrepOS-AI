from __future__ import annotations

from uuid import uuid4

from prepos.application.agents.critic_agent import CriticAgent
from prepos.application.agents.models import AgentResult, AgentSource


def test_critic_passes_supported_answer() -> None:
    critic = CriticAgent()
    results = [
        AgentResult(
            success=True,
            confidence="high",
            reasoning="Forecast: success probability 72%.",
            data={"probability_of_success": 72.0},
            sources=[AgentSource(label="Forecasting", reference="GET /forecasting/current")],
            tool_name="forecasting",
        )
    ]
    critique = critic.review(
        execution_id=uuid4(),
        answer="Forecast: success probability 72%.",
        results=results,
        sources=results[0].sources,
    )
    assert critique.passed is True
    assert not critique.unsupported_claims


def test_critic_flags_missing_citations() -> None:
    critic = CriticAgent()
    results = [
        AgentResult(
            success=True,
            confidence="high",
            reasoning="Loaded recommendations.",
            data={"recommendations": []},
            tool_name="recommendation",
        )
    ]
    critique = critic.review(
        execution_id=uuid4(),
        answer="Top recommendation: Federalism.",
        results=results,
        sources=[],
    )
    assert critique.citation_issues
    assert critique.passed is False
