from __future__ import annotations

from datetime import datetime
from uuid import UUID

from prepos.application.agents.models import (
    AgentCritiqueRecord,
    AgentExecutionGraph,
    AgentLearningSignal,
    AgentReflectionRecord,
    AgentTask,
)


class AgentRepositoryPort:
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
        raise NotImplementedError

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        raise NotImplementedError

    async def export_executions(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]:
        raise NotImplementedError

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
        raise NotImplementedError

    async def record_workflow_event(
        self,
        *,
        tenant_id: UUID,
        workflow_id: UUID | None,
        event_type: str,
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID:
        raise NotImplementedError

    async def save_critique(
        self,
        *,
        tenant_id: UUID,
        execution_id: UUID,
        critique: AgentCritiqueRecord,
        now: datetime,
    ) -> UUID:
        raise NotImplementedError

    async def save_reflection(
        self,
        *,
        tenant_id: UUID,
        execution_id: UUID,
        reflection: AgentReflectionRecord,
        now: datetime,
    ) -> UUID:
        raise NotImplementedError

    async def save_execution_graph(
        self,
        *,
        tenant_id: UUID,
        execution_id: UUID,
        graph: AgentExecutionGraph,
        now: datetime,
    ) -> None:
        raise NotImplementedError

    async def save_learning_signals(
        self,
        *,
        tenant_id: UUID,
        signals: list[AgentLearningSignal],
        now: datetime,
    ) -> list[UUID]:
        raise NotImplementedError

    async def list_learning_signals(
        self,
        *,
        tenant_id: UUID,
        signal_type: str | None = None,
        limit: int = 50,
    ) -> list[AgentLearningSignal]:
        raise NotImplementedError

    async def get_agent_health(self, *, tenant_id: UUID) -> list[dict[str, object]]:
        raise NotImplementedError
