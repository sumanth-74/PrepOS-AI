from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.agents.models import (
    AgentCritiqueRecord,
    AgentExecutionGraph,
    AgentLearningSignal,
    AgentReflectionRecord,
    AgentTask,
)
from prepos.application.agents.ports import AgentRepositoryPort
from prepos.infrastructure.db.models.agent_execution import (
    AgentExecutionModel,
    AgentTaskModel,
    AgentWorkflowEventModel,
    AgentWorkflowModel,
)
from prepos.infrastructure.db.models.agent_platform import (
    AgentCritiqueModel,
    AgentExecutionGraphNodeModel,
    AgentLearningSignalModel,
    AgentReflectionModel,
)


class SqlAlchemyAgentRepository(AgentRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_execution(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        agent_type: str,
        persona: str,
        objective: str,
        plan_json: dict[str, object],
        results_json: list[dict[str, object]],
        confidence: str,
        execution_time_ms: int,
        success: bool,
        task: AgentTask,
        now: datetime,
    ) -> UUID:
        execution_id = uuid4()
        self._session.add(
            AgentExecutionModel(
                id=execution_id,
                tenant_id=tenant_id,
                user_id=user_id,
                agent_type=agent_type,
                persona=persona,
                objective=objective,
                plan_json=plan_json,
                results_json=results_json,
                confidence=confidence,
                execution_time_ms=execution_time_ms,
                success=success,
                metadata_json={"task_id": str(task.task_id)},
                created_at=now,
            )
        )
        self._session.add(
            AgentTaskModel(
                id=task.task_id,
                tenant_id=tenant_id,
                execution_id=execution_id,
                objective=task.objective,
                requested_by=task.requested_by,
                persona=task.persona,
                priority=task.priority,
                status="completed" if success else "failed",
                metadata_json={},
                created_at=now,
            )
        )
        await self._session.flush()
        return execution_id

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        since = datetime.now(UTC) - timedelta(days=30)
        total_stmt = select(func.count()).select_from(AgentExecutionModel).where(
            AgentExecutionModel.tenant_id == tenant_id
        )
        total = int((await self._session.execute(total_stmt)).scalar_one())
        recent_stmt = select(func.count()).select_from(AgentExecutionModel).where(
            AgentExecutionModel.tenant_id == tenant_id,
            AgentExecutionModel.created_at >= since,
        )
        recent = int((await self._session.execute(recent_stmt)).scalar_one())
        success_stmt = select(func.count()).select_from(AgentExecutionModel).where(
            AgentExecutionModel.tenant_id == tenant_id,
            AgentExecutionModel.success.is_(True),
        )
        success_count = int((await self._session.execute(success_stmt)).scalar_one())

        agent_stmt = (
            select(AgentExecutionModel.agent_type, func.count())
            .where(AgentExecutionModel.tenant_id == tenant_id)
            .group_by(AgentExecutionModel.agent_type)
        )
        agent_rows = (await self._session.execute(agent_stmt)).all()

        recent_exec_stmt = (
            select(AgentExecutionModel)
            .where(AgentExecutionModel.tenant_id == tenant_id)
            .order_by(AgentExecutionModel.created_at.desc())
            .limit(10)
        )
        recent_rows = (await self._session.execute(recent_exec_stmt)).scalars().all()

        tool_usage: dict[str, int] = {}
        for row in recent_rows:
            for result in row.results_json:
                tool_name = result.get("tool_name")
                if tool_name:
                    tool_usage[str(tool_name)] = tool_usage.get(str(tool_name), 0) + 1

        workflow_stmt = (
            select(AgentWorkflowModel.workflow_type, func.count())
            .where(AgentWorkflowModel.tenant_id == tenant_id)
            .group_by(AgentWorkflowModel.workflow_type)
        )
        workflow_rows = (await self._session.execute(workflow_stmt)).all()

        critique_count_stmt = select(func.count()).select_from(AgentCritiqueModel).where(
            AgentCritiqueModel.tenant_id == tenant_id
        )
        critique_count = int((await self._session.execute(critique_count_stmt)).scalar_one())
        reflection_count_stmt = select(func.count()).select_from(AgentReflectionModel).where(
            AgentReflectionModel.tenant_id == tenant_id
        )
        reflection_count = int((await self._session.execute(reflection_count_stmt)).scalar_one())
        critique_avg_stmt = select(func.avg(AgentCritiqueModel.overall_score)).where(
            AgentCritiqueModel.tenant_id == tenant_id
        )
        critique_avg = (await self._session.execute(critique_avg_stmt)).scalar_one()

        confidence_map = {"high": 1.0, "medium": 0.7, "low": 0.4}
        avg_confidence = 0.0
        if total:
            rows = (
                await self._session.execute(
                    select(AgentExecutionModel.confidence).where(AgentExecutionModel.tenant_id == tenant_id)
                )
            ).all()
            avg_confidence = round(
                sum(confidence_map.get(str(row[0]), 0.5) for row in rows) / total,
                4,
            )

        return {
            "total_executions": total,
            "executions_last_30_days": recent,
            "success_rate": round(success_count / total, 4) if total else 0.0,
            "average_confidence_score": avg_confidence,
            "agent_usage": {row[0]: row[1] for row in agent_rows},
            "tool_usage": tool_usage,
            "workflow_counts": {row[0]: row[1] for row in workflow_rows},
            "critique_count": critique_count,
            "reflection_count": reflection_count,
            "average_critique_score": round(float(critique_avg or 0.0), 4),
            "recent_executions": [
                {
                    "execution_id": str(row.id),
                    "agent_type": row.agent_type,
                    "persona": row.persona,
                    "confidence": row.confidence,
                    "success": row.success,
                    "execution_time_ms": row.execution_time_ms,
                    "created_at": row.created_at.isoformat(),
                }
                for row in recent_rows
            ],
        }

    async def export_executions(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]:
        stmt = (
            select(AgentExecutionModel)
            .where(AgentExecutionModel.tenant_id == tenant_id)
            .order_by(AgentExecutionModel.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            {
                "execution_id": str(row.id),
                "agent_type": row.agent_type,
                "persona": row.persona,
                "objective": row.objective,
                "confidence": row.confidence,
                "success": row.success,
                "execution_time_ms": row.execution_time_ms,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]

    async def save_workflow(
        self,
        *,
        tenant_id: UUID,
        workflow_type: str,
        trigger_event: str,
        subject_key: str,
        plan_json: dict[str, object],
        results_json: list[dict[str, object]],
        now: datetime,
    ) -> UUID:
        workflow_id = uuid4()
        self._session.add(
            AgentWorkflowModel(
                id=workflow_id,
                tenant_id=tenant_id,
                workflow_type=workflow_type,
                status="completed",
                trigger_event=trigger_event,
                subject_key=subject_key,
                plan_json=plan_json,
                results_json=results_json,
                metadata_json={},
                created_at=now,
                completed_at=now,
            )
        )
        await self._session.flush()
        return workflow_id

    async def record_workflow_event(
        self,
        *,
        tenant_id: UUID,
        workflow_id: UUID | None,
        event_type: str,
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID:
        event_id = uuid4()
        self._session.add(
            AgentWorkflowEventModel(
                id=event_id,
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                event_type=event_type,
                metadata_json=metadata_json,
                created_at=now,
            )
        )
        await self._session.flush()
        return event_id

    async def save_critique(
        self,
        *,
        tenant_id: UUID,
        execution_id: UUID,
        critique: AgentCritiqueRecord,
        now: datetime,
    ) -> UUID:
        self._session.add(
            AgentCritiqueModel(
                id=critique.critique_id,
                tenant_id=tenant_id,
                execution_id=execution_id,
                overall_score=critique.overall_score,
                unsupported_claims=critique.unsupported_claims,
                citation_issues=critique.citation_issues,
                critique_json={
                    "passed": critique.passed,
                    "reasoning": critique.reasoning,
                },
                created_at=now,
            )
        )
        await self._session.flush()
        return critique.critique_id

    async def save_reflection(
        self,
        *,
        tenant_id: UUID,
        execution_id: UUID,
        reflection: AgentReflectionRecord,
        now: datetime,
    ) -> UUID:
        self._session.add(
            AgentReflectionModel(
                id=reflection.reflection_id,
                tenant_id=tenant_id,
                execution_id=execution_id,
                critique_id=reflection.critique_id,
                original_answer=reflection.original_answer,
                refined_answer=reflection.refined_answer,
                improvements_json=reflection.improvements,
                created_at=now,
            )
        )
        await self._session.flush()
        return reflection.reflection_id

    async def save_execution_graph(
        self,
        *,
        tenant_id: UUID,
        execution_id: UUID,
        graph: AgentExecutionGraph,
        now: datetime,
    ) -> None:
        for node in graph.nodes:
            self._session.add(
                AgentExecutionGraphNodeModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    execution_id=execution_id,
                    node_id=node.node_id,
                    parent_node_id=node.parent_node_id,
                    agent_type=node.agent_type,
                    tool_name=node.tool_name,
                    step_order=node.step_order,
                    status=node.status,
                    result_json=node.result.model_dump(mode="json") if node.result else {},
                    created_at=now,
                )
            )
        await self._session.flush()

    async def save_learning_signals(
        self,
        *,
        tenant_id: UUID,
        signals: list[AgentLearningSignal],
        now: datetime,
    ) -> list[UUID]:
        ids: list[UUID] = []
        for signal in signals:
            signal_id = uuid4()
            self._session.add(
                AgentLearningSignalModel(
                    id=signal_id,
                    tenant_id=tenant_id,
                    signal_type=signal.signal_type,
                    subject_key=signal.subject_key,
                    concept_id=signal.concept_id,
                    effectiveness_score=signal.effectiveness_score,
                    signal_json={
                        "explanation": signal.explanation,
                        "metadata": signal.metadata,
                    },
                    created_at=now,
                )
            )
            ids.append(signal_id)
        await self._session.flush()
        return ids

    async def list_learning_signals(
        self,
        *,
        tenant_id: UUID,
        signal_type: str | None = None,
        limit: int = 50,
    ) -> list[AgentLearningSignal]:
        stmt = select(AgentLearningSignalModel).where(AgentLearningSignalModel.tenant_id == tenant_id)
        if signal_type is not None:
            stmt = stmt.where(AgentLearningSignalModel.signal_type == signal_type)
        stmt = stmt.order_by(AgentLearningSignalModel.created_at.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            AgentLearningSignal(
                signal_type=row.signal_type,
                subject_key=row.subject_key,
                concept_id=row.concept_id,
                effectiveness_score=row.effectiveness_score,
                explanation=str(row.signal_json.get("explanation", "")),
                metadata=dict(row.signal_json.get("metadata", {})),
            )
            for row in rows
        ]

    async def get_agent_health(self, *, tenant_id: UUID) -> list[dict[str, object]]:
        metrics = await self.get_admin_metrics(tenant_id=tenant_id)
        from prepos.application.agents.agent_marketplace import AgentMarketplace

        return [
            item.model_dump(mode="json")
            for item in AgentMarketplace.build_health_status(metrics)
        ]
