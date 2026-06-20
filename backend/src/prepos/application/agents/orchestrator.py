from __future__ import annotations

import time
from datetime import UTC, datetime
from uuid import uuid4

import structlog

from prepos.application.agents.agent_marketplace import AgentMarketplace
from prepos.application.agents.agent_memory_context import AgentMemoryContextBuilder
from prepos.application.agents.collaboration_executor import CollaborationExecutor
from prepos.application.agents.critic_agent import CriticAgent
from prepos.application.agents.learning_loop_service import AgentLearningLoopService
from prepos.application.agents.models import (
    AgentContext,
    AgentOrchestratorResponse,
    AgentResult,
    AgentSource,
    AgentTask,
)
from prepos.application.agents.planner_agent import PlannerAgent
from prepos.application.agents.ports import AgentRepositoryPort
from prepos.application.agents.reflection_agent import ReflectionAgent
from prepos.application.agents.registry import ToolRegistry

logger = structlog.get_logger(__name__)


class AgentOrchestrator:
    def __init__(
        self,
        *,
        repository: AgentRepositoryPort,
        tool_registry: ToolRegistry,
        memory_builder: AgentMemoryContextBuilder | None = None,
        learning_loop: AgentLearningLoopService | None = None,
        trace_service=None,
    ) -> None:
        self._repository = repository
        self._tools = tool_registry
        self._planner = PlannerAgent()
        self._memory_builder = memory_builder or AgentMemoryContextBuilder()
        self._learning_loop = learning_loop
        self._trace_service = trace_service
        self._marketplace = AgentMarketplace(tool_registry=tool_registry)
        self._collaborator = CollaborationExecutor(marketplace=self._marketplace)
        self._critic = CriticAgent()
        self._reflection = ReflectionAgent()

    async def execute(
        self,
        *,
        tenant_id,
        user_id,
        persona: str,
        question: str,
        student_id=None,
        student_user_id=None,
        exam_id: str | None = None,
    ) -> AgentOrchestratorResponse:
        started = time.perf_counter()
        memory_context = await self._memory_builder.build(
            tenant_id=tenant_id,
            user_id=user_id,
            persona=persona,
            student_user_id=student_user_id,
        )
        learning_signals = []
        if self._learning_loop is not None:
            learning_signals = await self._learning_loop.build_signals(
                tenant_id=tenant_id,
                subject_key=str(student_id or user_id),
                student_id=student_id,
            )

        context = AgentContext(
            tenant_id=tenant_id,
            user_id=user_id,
            persona=persona,
            question=question,
            student_id=student_id,
            student_user_id=student_user_id,
            exam_id=exam_id,
            memory_context=memory_context,
            learning_signals=learning_signals,
        )

        preferred = self._marketplace.select_for_objective(objective=question, persona=persona)
        plan = self._planner.plan(
            objective=question,
            persona=persona,
            learning_signals=learning_signals,
            preferred_coordinator=preferred,
        )
        coordinator = preferred or self._planner.coordinator_for_persona(persona, question)
        task = AgentTask(
            task_id=uuid4(),
            objective=question,
            requested_by=user_id,
            persona=persona,
        )
        logger.info(
            "agent_execution_started",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            agent_type=coordinator,
            persona=persona,
        )

        agent_result, execution_graph, collaborating_agents = await self._collaborator.execute_plan(
            context=context,
            plan=plan,
            coordinator_agent=coordinator,
        )

        child_results: list[AgentResult] = []
        if agent_result.data.get("tool_results"):
            for payload in agent_result.data["tool_results"]:
                child_results.append(AgentResult.model_validate(payload))
        else:
            child_results = [agent_result]

        draft_answer = agent_result.reasoning
        elapsed_ms = max(0, int((time.perf_counter() - started) * 1000))
        execution_id = await self._repository.save_execution(
            tenant_id=tenant_id,
            user_id=user_id,
            agent_type=coordinator,
            persona=persona,
            objective=question,
            plan_json=plan.model_dump(mode="json"),
            results_json=[item.model_dump(mode="json") for item in child_results],
            confidence=agent_result.confidence,
            execution_time_ms=elapsed_ms,
            success=agent_result.success,
            task=task,
            now=datetime.now(UTC),
        )
        execution_graph.execution_id = execution_id
        await self._repository.save_execution_graph(
            tenant_id=tenant_id,
            execution_id=execution_id,
            graph=execution_graph,
            now=datetime.now(UTC),
        )

        critique = self._critic.review(
            execution_id=execution_id,
            answer=draft_answer,
            results=child_results,
            sources=agent_result.sources,
        )
        await self._repository.save_critique(
            tenant_id=tenant_id,
            execution_id=execution_id,
            critique=critique,
            now=datetime.now(UTC),
        )

        final_answer = draft_answer
        reflection_record = self._reflection.reflect(
            execution_id=execution_id,
            critique=critique,
            original_answer=draft_answer,
            results=child_results,
        )
        if reflection_record is not None:
            await self._repository.save_reflection(
                tenant_id=tenant_id,
                execution_id=execution_id,
                reflection=reflection_record,
                now=datetime.now(UTC),
            )
            final_answer = reflection_record.refined_answer

        response = AgentOrchestratorResponse(
            agent_used=coordinator,
            confidence=agent_result.confidence if critique.passed else "medium",
            answer=final_answer,
            results=child_results,
            sources=agent_result.sources,
            plan=plan,
            execution_id=execution_id,
            critique=critique,
            reflection=reflection_record,
            execution_graph=execution_graph,
            collaborating_agents=collaborating_agents,
        )
        if self._trace_service is not None:
            trace_id = await self._trace_service.record_execution(
                tenant_id=tenant_id,
                user_id=user_id,
                persona=persona,
                question=question,
                latency_ms=elapsed_ms,
                response=response,
            )
            response.trace_id = trace_id
        logger.info(
            "agent_execution_completed",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            agent_type=coordinator,
            execution_time_ms=elapsed_ms,
            confidence=response.confidence,
            critique_passed=critique.passed,
            collaborating_agents=collaborating_agents,
        )
        return response
