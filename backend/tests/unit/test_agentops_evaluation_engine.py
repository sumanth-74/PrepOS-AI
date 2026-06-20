from __future__ import annotations

from uuid import uuid4

from prepos.application.agentops.evaluation_engine import AgentEvaluationEngine
from prepos.application.agents.models import (
    AgentCritiqueRecord,
    AgentExecutionPlan,
    AgentOrchestratorResponse,
    AgentPlanStep,
    AgentResult,
    AgentSource,
)


def test_evaluation_engine_scores_orchestrator_response() -> None:
    engine = AgentEvaluationEngine()
    execution_id = uuid4()
    trace_id = uuid4()
    response = AgentOrchestratorResponse(
        agent_used="student_success_agent",
        confidence="high",
        answer="Forecast: success probability 72%.",
        results=[
            AgentResult(
                success=True,
                confidence="high",
                reasoning="Forecast loaded.",
                tool_name="forecasting",
                sources=[AgentSource(label="Forecasting", reference="GET /forecasting/current")],
            )
        ],
        sources=[AgentSource(label="Forecasting", reference="GET /forecasting/current")],
        plan=AgentExecutionPlan(
            plan_id=uuid4(),
            objective="How can I improve readiness?",
            persona="student",
            steps=[
                AgentPlanStep(
                    step_order=1,
                    agent_type="forecasting_agent",
                    tool_names=["forecasting"],
                    objective="forecast",
                )
            ],
        ),
        execution_id=execution_id,
        critique=AgentCritiqueRecord(
            critique_id=uuid4(),
            execution_id=execution_id,
            overall_score=0.9,
            passed=True,
        ),
    )
    scores = engine.evaluate(response=response, trace_id=trace_id)
    assert scores.support_score == 1.0
    assert scores.citation_score == 1.0
    assert scores.planner_quality_score >= 0.9
