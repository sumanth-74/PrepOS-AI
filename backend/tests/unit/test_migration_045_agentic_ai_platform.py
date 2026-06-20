from __future__ import annotations

from prepos.infrastructure.db.models.agent_platform import (
    AgentCritiqueModel,
    AgentExecutionGraphNodeModel,
    AgentLearningSignalModel,
    AgentReflectionModel,
)


def test_migration_045_models_have_expected_columns() -> None:
    critique_columns = {column.name for column in AgentCritiqueModel.__table__.columns}
    assert critique_columns >= {
        "id",
        "tenant_id",
        "execution_id",
        "overall_score",
        "unsupported_claims",
        "citation_issues",
        "created_at",
    }

    reflection_columns = {column.name for column in AgentReflectionModel.__table__.columns}
    assert reflection_columns >= {
        "id",
        "tenant_id",
        "execution_id",
        "critique_id",
        "original_answer",
        "refined_answer",
        "created_at",
    }

    graph_columns = {column.name for column in AgentExecutionGraphNodeModel.__table__.columns}
    assert graph_columns >= {
        "id",
        "tenant_id",
        "execution_id",
        "node_id",
        "agent_type",
        "step_order",
        "status",
        "created_at",
    }

    signal_columns = {column.name for column in AgentLearningSignalModel.__table__.columns}
    assert signal_columns >= {
        "id",
        "tenant_id",
        "signal_type",
        "subject_key",
        "effectiveness_score",
        "created_at",
    }


def test_agentic_ai_platform_migration_chains_to_traces() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revision = script.get_revision("045_agentic_ai_platform")
    assert revision is not None
    assert revision.down_revision == "044_agent_execution_framework"
    next_revision = script.get_revision("046_agent_traces")
    assert next_revision is not None
    assert next_revision.down_revision == "045_agentic_ai_platform"
