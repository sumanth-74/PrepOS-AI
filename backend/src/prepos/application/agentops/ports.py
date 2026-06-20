from __future__ import annotations

from datetime import datetime
from uuid import UUID

from prepos.application.agentops.models import (
    AgentBenchmarkRecord,
    AgentCostRecord,
    AgentEvaluationScores,
    AgentFeedbackAnalyticsResponse,
    AgentFeedbackRequest,
    AgentHealthDetailResponse,
    AgentTraceArtifactRecord,
    AgentTraceRecord,
    AgentTraceStepRecord,
    ExperimentRecord,
    ExperimentVariantRecord,
    PendingActionRecord,
    PromptRecord,
)


class AgentOpsRepositoryPort:
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
        raise NotImplementedError

    async def list_traces(self, *, tenant_id: UUID, limit: int, offset: int) -> tuple[list[AgentTraceRecord], int]:
        raise NotImplementedError

    async def get_trace(self, *, tenant_id: UUID, trace_id: UUID) -> AgentTraceRecord | None:
        raise NotImplementedError

    async def export_trace(self, *, tenant_id: UUID, trace_id: UUID) -> dict[str, object] | None:
        raise NotImplementedError

    async def save_evaluation(self, *, tenant_id: UUID, scores: AgentEvaluationScores, now: datetime) -> UUID:
        raise NotImplementedError

    async def get_evaluation_dashboard(self, *, tenant_id: UUID) -> dict[str, object]:
        raise NotImplementedError

    async def save_benchmark(self, *, record: AgentBenchmarkRecord) -> UUID:
        raise NotImplementedError

    async def list_benchmarks(self, *, tenant_id: UUID | None, limit: int) -> list[AgentBenchmarkRecord]:
        raise NotImplementedError

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
        raise NotImplementedError

    async def get_feedback_analytics(self, *, tenant_id: UUID) -> AgentFeedbackAnalyticsResponse:
        raise NotImplementedError

    async def save_cost(self, *, tenant_id: UUID, record: AgentCostRecord, trace_id: UUID | None, execution_id: UUID | None, now: datetime) -> UUID:
        raise NotImplementedError

    async def get_cost_dashboard(self, *, tenant_id: UUID) -> dict[str, object]:
        raise NotImplementedError

    async def create_pending_action(self, *, tenant_id: UUID, action: PendingActionRecord, now: datetime) -> UUID:
        raise NotImplementedError

    async def list_pending_actions(self, *, tenant_id: UUID, status: str | None, limit: int) -> tuple[list[PendingActionRecord], int]:
        raise NotImplementedError

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
        raise NotImplementedError

    async def list_experiments(self, *, tenant_id: UUID | None) -> list[ExperimentRecord]:
        raise NotImplementedError

    async def list_prompts(self, *, tenant_id: UUID | None) -> list[PromptRecord]:
        raise NotImplementedError

    async def get_agent_health_details(self, *, tenant_id: UUID) -> list[AgentHealthDetailResponse]:
        raise NotImplementedError
