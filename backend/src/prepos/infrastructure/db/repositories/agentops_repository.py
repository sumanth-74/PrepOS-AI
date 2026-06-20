from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.agentops.models import (
    AgentBenchmarkRecord,
    AgentCostDashboardResponse,
    AgentCostRecord,
    AgentEvaluationDashboardResponse,
    AgentEvaluationScores,
    AgentFeedbackAnalyticsResponse,
    AgentFeedbackRequest,
    AgentHealthDetailResponse,
    AgentTraceArtifactRecord,
    AgentTraceRecord,
    AgentTraceStepRecord,
    ExperimentRecord,
    PendingActionRecord,
    PromptRecord,
)
from prepos.application.agentops.ports import AgentOpsRepositoryPort
from prepos.infrastructure.db.models.agentops import (
    AgentBenchmarkModel,
    AgentCostModel,
    AgentEvaluationModel,
    AgentFeedbackModel,
    AgentTraceArtifactModel,
    AgentTraceModel,
    AgentTraceStepModel,
    ExperimentModel,
    PendingActionModel,
    PromptModel,
    PromptVersionModel,
)
from prepos.infrastructure.db.models.agent_execution import AgentExecutionModel


class SqlAlchemyAgentOpsRepository(AgentOpsRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_trace(
        self,
        *,
        tenant_id: UUID,
        execution_id: UUID,
        user_id: UUID,
        persona: str,
        question: str,
        answer: str,
        confidence: str,
        latency_ms: int,
        steps: list[AgentTraceStepRecord],
        artifacts: list[AgentTraceArtifactRecord],
        now: datetime,
    ) -> UUID:
        trace_id = uuid4()
        self._session.add(
            AgentTraceModel(
                id=trace_id,
                tenant_id=tenant_id,
                execution_id=execution_id,
                user_id=user_id,
                persona=persona,
                question=question,
                answer=answer,
                confidence=confidence,
                latency_ms=latency_ms,
                created_at=now,
            )
        )
        for step in steps:
            self._session.add(
                AgentTraceStepModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    trace_id=trace_id,
                    step_number=step.step_number,
                    agent_name=step.agent_name,
                    tool_name=step.tool_name,
                    input_json=step.input_json,
                    output_json=step.output_json,
                    latency_ms=step.latency_ms,
                    status=step.status,
                    created_at=now,
                )
            )
        for artifact in artifacts:
            self._session.add(
                AgentTraceArtifactModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    trace_id=trace_id,
                    artifact_type=artifact.artifact_type,
                    artifact_json=artifact.artifact_json,
                    created_at=now,
                )
            )
        await self._session.flush()
        return trace_id

    async def list_traces(self, *, tenant_id: UUID, limit: int, offset: int) -> tuple[list[AgentTraceRecord], int]:
        total = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(AgentTraceModel).where(AgentTraceModel.tenant_id == tenant_id)
                )
            ).scalar_one()
        )
        rows = (
            await self._session.execute(
                select(AgentTraceModel)
                .where(AgentTraceModel.tenant_id == tenant_id)
                .order_by(AgentTraceModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        ).scalars().all()
        return [self._map_trace(row, steps=[], artifacts=[]) for row in rows], total

    async def get_trace(self, *, tenant_id: UUID, trace_id: UUID) -> AgentTraceRecord | None:
        row = (
            await self._session.execute(
                select(AgentTraceModel).where(
                    AgentTraceModel.tenant_id == tenant_id,
                    AgentTraceModel.id == trace_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        steps = (
            await self._session.execute(
                select(AgentTraceStepModel)
                .where(AgentTraceStepModel.trace_id == trace_id)
                .order_by(AgentTraceStepModel.step_number)
            )
        ).scalars().all()
        artifacts = (
            await self._session.execute(
                select(AgentTraceArtifactModel).where(AgentTraceArtifactModel.trace_id == trace_id)
            )
        ).scalars().all()
        return self._map_trace(
            row,
            steps=[
                AgentTraceStepRecord(
                    step_number=step.step_number,
                    agent_name=step.agent_name,
                    tool_name=step.tool_name,
                    input_json=step.input_json,
                    output_json=step.output_json,
                    latency_ms=step.latency_ms,
                    status=step.status,
                )
                for step in steps
            ],
            artifacts=[
                AgentTraceArtifactRecord(artifact_type=item.artifact_type, artifact_json=item.artifact_json)
                for item in artifacts
            ],
        )

    async def export_trace(self, *, tenant_id: UUID, trace_id: UUID) -> dict[str, object] | None:
        trace = await self.get_trace(tenant_id=tenant_id, trace_id=trace_id)
        if trace is None:
            return None
        return json.loads(trace.model_dump_json())

    @staticmethod
    def _map_trace(row: AgentTraceModel, *, steps: list[AgentTraceStepRecord], artifacts: list[AgentTraceArtifactRecord]) -> AgentTraceRecord:
        return AgentTraceRecord(
            trace_id=row.id,
            tenant_id=row.tenant_id,
            execution_id=row.execution_id,
            user_id=row.user_id,
            persona=row.persona,
            question=row.question,
            answer=row.answer,
            confidence=row.confidence,
            latency_ms=row.latency_ms,
            created_at=row.created_at,
            steps=steps,
            artifacts=artifacts,
        )

    async def save_evaluation(self, *, tenant_id: UUID, scores: AgentEvaluationScores, now: datetime) -> UUID:
        evaluation_id = scores.evaluation_id
        self._session.add(
            AgentEvaluationModel(
                id=evaluation_id,
                tenant_id=tenant_id,
                trace_id=scores.trace_id,
                execution_id=scores.execution_id,
                retrieval_score=scores.retrieval_score,
                citation_score=scores.citation_score,
                hallucination_score=scores.hallucination_score,
                support_score=scores.support_score,
                answer_quality_score=scores.answer_quality_score,
                planner_quality_score=scores.planner_quality_score,
                evaluation_json=scores.details,
                created_at=now,
            )
        )
        await self._session.flush()
        return evaluation_id

    async def get_evaluation_dashboard(self, *, tenant_id: UUID) -> dict[str, object]:
        rows = (
            await self._session.execute(
                select(AgentEvaluationModel)
                .where(AgentEvaluationModel.tenant_id == tenant_id)
                .order_by(AgentEvaluationModel.created_at.desc())
                .limit(20)
            )
        ).scalars().all()
        if not rows:
            return AgentEvaluationDashboardResponse(
                average_retrieval_score=0.0,
                average_citation_score=0.0,
                average_hallucination_score=0.0,
                average_support_score=0.0,
                average_answer_quality_score=0.0,
                average_planner_quality_score=0.0,
                recent_evaluations=[],
                total_evaluations=0,
            ).model_dump(mode="json")

        def avg(field: str) -> float:
            return round(sum(getattr(row, field) for row in rows) / len(rows), 4)

        recent = [
            AgentEvaluationScores(
                evaluation_id=row.id,
                trace_id=row.trace_id,
                execution_id=row.execution_id,
                retrieval_score=row.retrieval_score,
                citation_score=row.citation_score,
                hallucination_score=row.hallucination_score,
                support_score=row.support_score,
                answer_quality_score=row.answer_quality_score,
                planner_quality_score=row.planner_quality_score,
                details=row.evaluation_json,
                created_at=row.created_at,
            )
            for row in rows
        ]
        total = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(AgentEvaluationModel).where(
                        AgentEvaluationModel.tenant_id == tenant_id
                    )
                )
            ).scalar_one()
        )
        return AgentEvaluationDashboardResponse(
            average_retrieval_score=avg("retrieval_score"),
            average_citation_score=avg("citation_score"),
            average_hallucination_score=avg("hallucination_score"),
            average_support_score=avg("support_score"),
            average_answer_quality_score=avg("answer_quality_score"),
            average_planner_quality_score=avg("planner_quality_score"),
            recent_evaluations=recent,
            total_evaluations=total,
        ).model_dump(mode="json")

    async def save_benchmark(self, *, record: AgentBenchmarkRecord) -> UUID:
        self._session.add(
            AgentBenchmarkModel(
                id=record.benchmark_id,
                tenant_id=None,
                benchmark_name=record.benchmark_name,
                suite_type=record.suite_type,
                status=record.status,
                scenario_count=record.scenario_count,
                passed_count=record.passed_count,
                failed_count=record.failed_count,
                results_json=record.results,
                created_at=record.created_at,
                completed_at=record.completed_at,
            )
        )
        await self._session.flush()
        return record.benchmark_id

    async def list_benchmarks(self, *, tenant_id: UUID | None, limit: int) -> list[AgentBenchmarkRecord]:
        stmt = select(AgentBenchmarkModel).order_by(AgentBenchmarkModel.created_at.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            AgentBenchmarkRecord(
                benchmark_id=row.id,
                benchmark_name=row.benchmark_name,
                suite_type=row.suite_type,
                status=row.status,
                scenario_count=row.scenario_count,
                passed_count=row.passed_count,
                failed_count=row.failed_count,
                results=row.results_json,
                created_at=row.created_at,
                completed_at=row.completed_at,
            )
            for row in rows
        ]

    async def save_feedback(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        request: AgentFeedbackRequest,
        agent_type: str | None,
        intent: str | None,
        now: datetime,
    ) -> UUID:
        feedback_id = uuid4()
        self._session.add(
            AgentFeedbackModel(
                id=feedback_id,
                tenant_id=tenant_id,
                trace_id=request.trace_id,
                execution_id=request.execution_id,
                user_id=user_id,
                rating=request.rating,
                feedback_text=request.feedback_text,
                agent_type=agent_type,
                intent=intent,
                created_at=now,
            )
        )
        await self._session.flush()
        return feedback_id

    async def get_feedback_analytics(self, *, tenant_id: UUID) -> AgentFeedbackAnalyticsResponse:
        rows = (
            await self._session.execute(select(AgentFeedbackModel).where(AgentFeedbackModel.tenant_id == tenant_id))
        ).scalars().all()
        total = len(rows)
        if total == 0:
            return AgentFeedbackAnalyticsResponse(
                feedback_rate=0.0,
                satisfaction_score=0.0,
                feedback_by_agent={},
                feedback_by_intent={},
                total_feedback=0,
            )
        helpful = sum(1 for row in rows if row.rating == "helpful")
        partial = sum(1 for row in rows if row.rating == "partially_helpful")
        by_agent: dict[str, int] = {}
        by_intent: dict[str, int] = {}
        for row in rows:
            if row.agent_type:
                by_agent[row.agent_type] = by_agent.get(row.agent_type, 0) + 1
            if row.intent:
                by_intent[row.intent] = by_intent.get(row.intent, 0) + 1
        return AgentFeedbackAnalyticsResponse(
            feedback_rate=round(total / max(total, 1), 4),
            satisfaction_score=round((helpful + partial * 0.5) / total, 4),
            feedback_by_agent=by_agent,
            feedback_by_intent=by_intent,
            total_feedback=total,
        )

    async def save_cost(
        self,
        *,
        tenant_id: UUID,
        record: AgentCostRecord,
        trace_id: UUID | None,
        execution_id: UUID | None,
        now: datetime,
    ) -> UUID:
        cost_id = uuid4()
        self._session.add(
            AgentCostModel(
                id=cost_id,
                tenant_id=tenant_id,
                trace_id=trace_id,
                execution_id=execution_id,
                agent_type=record.agent_type,
                workflow_type=record.workflow_type,
                tokens_in=record.tokens_in,
                tokens_out=record.tokens_out,
                estimated_cost=record.estimated_cost,
                latency_ms=record.latency_ms,
                created_at=now,
            )
        )
        await self._session.flush()
        return cost_id

    async def get_cost_dashboard(self, *, tenant_id: UUID) -> dict[str, object]:
        since = datetime.now(UTC) - timedelta(days=1)
        rows = (
            await self._session.execute(
                select(AgentCostModel).where(
                    AgentCostModel.tenant_id == tenant_id,
                    AgentCostModel.created_at >= since,
                )
            )
        ).scalars().all()
        if not rows:
            return AgentCostDashboardResponse(
                daily_cost=0.0,
                cost_per_query=0.0,
                total_queries=0,
                cost_by_agent={},
                slowest_workflows=[],
                highest_cost_agents=[],
            ).model_dump(mode="json")
        daily_cost = round(sum(row.estimated_cost for row in rows), 6)
        total_queries = len(rows)
        cost_by_agent: dict[str, float] = {}
        for row in rows:
            cost_by_agent[row.agent_type] = round(cost_by_agent.get(row.agent_type, 0.0) + row.estimated_cost, 6)
        highest = sorted(
            [
                AgentCostRecord(
                    agent_type=agent,
                    tokens_in=0,
                    tokens_out=0,
                    estimated_cost=cost,
                    latency_ms=0,
                    query_count=sum(1 for row in rows if row.agent_type == agent),
                )
                for agent, cost in cost_by_agent.items()
            ],
            key=lambda item: item.estimated_cost,
            reverse=True,
        )
        slowest = sorted(
            [
                {
                    "workflow_type": row.workflow_type or "orchestrator",
                    "agent_type": row.agent_type,
                    "latency_ms": row.latency_ms,
                }
                for row in rows
            ],
            key=lambda item: item["latency_ms"],
            reverse=True,
        )[:5]
        return AgentCostDashboardResponse(
            daily_cost=daily_cost,
            cost_per_query=round(daily_cost / total_queries, 6),
            total_queries=total_queries,
            cost_by_agent=cost_by_agent,
            slowest_workflows=slowest,
            highest_cost_agents=highest[:5],
        ).model_dump(mode="json")

    async def create_pending_action(self, *, tenant_id: UUID, action: PendingActionRecord, now: datetime) -> UUID:
        self._session.add(
            PendingActionModel(
                id=action.action_id,
                tenant_id=tenant_id,
                action_type=action.action_type,
                proposed_by_agent=action.proposed_by_agent,
                subject_key=action.subject_key,
                explanation=action.explanation,
                payload_json=action.payload,
                status=action.status,
                created_at=now,
            )
        )
        await self._session.flush()
        return action.action_id

    async def list_pending_actions(
        self,
        *,
        tenant_id: UUID,
        status: str | None,
        limit: int,
    ) -> tuple[list[PendingActionRecord], int]:
        stmt = select(PendingActionModel).where(PendingActionModel.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(PendingActionModel.status == status)
        count_stmt = select(func.count()).select_from(PendingActionModel).where(PendingActionModel.tenant_id == tenant_id)
        if status:
            count_stmt = count_stmt.where(PendingActionModel.status == status)
        total = int((await self._session.execute(count_stmt)).scalar_one())
        rows = (
            await self._session.execute(stmt.order_by(PendingActionModel.created_at.desc()).limit(limit))
        ).scalars().all()
        return [self._map_pending(row) for row in rows], total

    async def update_pending_action_status(
        self,
        *,
        tenant_id: UUID,
        action_id: UUID,
        status: str,
        reviewed_by_user_id: UUID,
        review_note: str | None,
        now: datetime,
    ) -> PendingActionRecord | None:
        row = (
            await self._session.execute(
                select(PendingActionModel).where(
                    PendingActionModel.tenant_id == tenant_id,
                    PendingActionModel.id == action_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        row.status = status
        row.reviewed_by_user_id = reviewed_by_user_id
        row.review_note = review_note
        row.reviewed_at = now
        await self._session.flush()
        return self._map_pending(row)

    @staticmethod
    def _map_pending(row: PendingActionModel) -> PendingActionRecord:
        return PendingActionRecord(
            action_id=row.id,
            action_type=row.action_type,
            proposed_by_agent=row.proposed_by_agent,
            subject_key=row.subject_key,
            explanation=row.explanation,
            payload=row.payload_json,
            status=row.status,
            created_at=row.created_at,
            reviewed_at=row.reviewed_at,
            review_note=row.review_note,
        )

    async def list_experiments(self, *, tenant_id: UUID | None) -> list[ExperimentRecord]:
        stmt = select(ExperimentModel).order_by(ExperimentModel.created_at.desc())
        if tenant_id is not None:
            stmt = stmt.where(ExperimentModel.tenant_id == tenant_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            ExperimentRecord(
                experiment_id=row.id,
                name=row.name,
                description=row.description,
                experiment_type=row.experiment_type,
                status=row.status,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def list_prompts(self, *, tenant_id: UUID | None) -> list[PromptRecord]:
        stmt = select(PromptModel).order_by(PromptModel.created_at.desc())
        rows = (await self._session.execute(stmt)).scalars().all()
        prompts: list[PromptRecord] = []
        for row in rows:
            version_label = None
            rollout = 100.0
            benchmark = None
            if row.active_version_id:
                version = (
                    await self._session.execute(
                        select(PromptVersionModel).where(PromptVersionModel.id == row.active_version_id)
                    )
                ).scalar_one_or_none()
                if version is not None:
                    version_label = version.version
                    rollout = version.rollout_pct
                    benchmark = version.benchmark_score
            prompts.append(
                PromptRecord(
                    prompt_id=row.id,
                    prompt_key=row.prompt_key,
                    description=row.description,
                    active_version=version_label,
                    rollout_pct=rollout,
                    benchmark_score=benchmark,
                )
            )
        return prompts

    async def get_agent_health_details(self, *, tenant_id: UUID) -> list[AgentHealthDetailResponse]:
        rows = (
            await self._session.execute(
                select(AgentExecutionModel).where(AgentExecutionModel.tenant_id == tenant_id)
            )
        ).scalars().all()
        feedback = await self.get_feedback_analytics(tenant_id=tenant_id)
        since = datetime.now(UTC) - timedelta(days=1)
        costs = (
            await self._session.execute(
                select(AgentCostModel).where(
                    AgentCostModel.tenant_id == tenant_id,
                    AgentCostModel.created_at >= since,
                )
            )
        ).scalars().all()
        grouped: dict[str, list[AgentExecutionModel]] = {}
        for row in rows:
            grouped.setdefault(row.agent_type, []).append(row)
        cost_by_agent: dict[str, float] = {}
        latency_by_agent: dict[str, list[int]] = {}
        for cost in costs:
            cost_by_agent[cost.agent_type] = cost_by_agent.get(cost.agent_type, 0.0) + cost.estimated_cost
            latency_by_agent.setdefault(cost.agent_type, []).append(cost.latency_ms)
        details: list[AgentHealthDetailResponse] = []
        for agent_type, executions in grouped.items():
            failures = sum(1 for item in executions if not item.success)
            avg_latency = (
                round(sum(latency_by_agent.get(agent_type, [0])) / max(len(latency_by_agent.get(agent_type, [1])), 1), 2)
            )
            confidence_map = {"high": 1.0, "medium": 0.7, "low": 0.4}
            avg_conf = round(
                sum(confidence_map.get(item.confidence, 0.5) for item in executions) / len(executions),
                4,
            )
            status = "healthy" if failures == 0 else "degraded"
            details.append(
                AgentHealthDetailResponse(
                    agent_type=agent_type,
                    executions=len(executions),
                    failures=failures,
                    retries=0,
                    average_latency_ms=avg_latency,
                    average_confidence_score=avg_conf,
                    satisfaction_score=feedback.satisfaction_score,
                    estimated_cost=round(cost_by_agent.get(agent_type, 0.0), 6),
                    status=status,
                )
            )
        return sorted(details, key=lambda item: item.executions, reverse=True)
