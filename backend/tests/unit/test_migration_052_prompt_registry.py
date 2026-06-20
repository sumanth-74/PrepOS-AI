from __future__ import annotations

from prepos.infrastructure.db.models.agentops import (
    AgentBenchmarkModel,
    AgentCostModel,
    AgentEvaluationModel,
    AgentFeedbackModel,
    AgentTraceArtifactModel,
    AgentTraceModel,
    AgentTraceStepModel,
    PendingActionModel,
    PromptModel,
    PromptVersionModel,
)


def test_migration_052_models_have_expected_columns() -> None:
    trace_columns = {column.name for column in AgentTraceModel.__table__.columns}
    assert trace_columns >= {"id", "tenant_id", "execution_id", "question", "answer", "latency_ms", "created_at"}

    step_columns = {column.name for column in AgentTraceStepModel.__table__.columns}
    assert step_columns >= {"trace_id", "step_number", "agent_name", "tool_name", "status"}

    artifact_columns = {column.name for column in AgentTraceArtifactModel.__table__.columns}
    assert artifact_columns >= {"trace_id", "artifact_type", "artifact_json"}

    evaluation_columns = {column.name for column in AgentEvaluationModel.__table__.columns}
    assert evaluation_columns >= {"retrieval_score", "citation_score", "hallucination_score", "planner_quality_score"}

    feedback_columns = {column.name for column in AgentFeedbackModel.__table__.columns}
    assert feedback_columns >= {"trace_id", "rating", "feedback_text"}

    cost_columns = {column.name for column in AgentCostModel.__table__.columns}
    assert cost_columns >= {"tokens_in", "tokens_out", "estimated_cost", "latency_ms"}

    pending_columns = {column.name for column in PendingActionModel.__table__.columns}
    assert pending_columns >= {"action_type", "proposed_by_agent", "status", "explanation"}

    prompt_columns = {column.name for column in PromptModel.__table__.columns}
    assert prompt_columns >= {"prompt_key", "description", "active_version_id"}

    version_columns = {column.name for column in PromptVersionModel.__table__.columns}
    assert version_columns >= {"prompt_id", "version", "content", "rollout_pct"}


def test_prompt_registry_migration_is_head() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    assert script.get_current_head() == "052_prompt_registry"
    revision = script.get_revision("052_prompt_registry")
    assert revision is not None
    assert revision.down_revision == "051_agent_experiments"
