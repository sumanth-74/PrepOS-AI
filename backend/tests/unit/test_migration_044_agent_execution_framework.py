from __future__ import annotations

from prepos.infrastructure.db.models.agent_execution import (
    AgentExecutionModel,
    AgentTaskModel,
    AgentWorkflowEventModel,
    AgentWorkflowModel,
)


def test_migration_044_models_have_expected_columns() -> None:
    execution_columns = {column.name for column in AgentExecutionModel.__table__.columns}
    assert execution_columns >= {
        "id",
        "tenant_id",
        "user_id",
        "agent_type",
        "persona",
        "objective",
        "plan_json",
        "results_json",
        "confidence",
        "execution_time_ms",
        "success",
        "created_at",
    }

    task_columns = {column.name for column in AgentTaskModel.__table__.columns}
    assert task_columns >= {
        "id",
        "tenant_id",
        "execution_id",
        "objective",
        "requested_by",
        "persona",
        "priority",
        "status",
        "created_at",
    }

    workflow_columns = {column.name for column in AgentWorkflowModel.__table__.columns}
    assert workflow_columns >= {
        "id",
        "tenant_id",
        "workflow_type",
        "status",
        "trigger_event",
        "subject_key",
        "plan_json",
        "results_json",
        "created_at",
    }

    event_columns = {column.name for column in AgentWorkflowEventModel.__table__.columns}
    assert event_columns >= {
        "id",
        "tenant_id",
        "workflow_id",
        "event_type",
        "metadata_json",
        "created_at",
    }


def test_agent_execution_migration_chains_to_agentic_platform() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revision = script.get_revision("044_agent_execution_framework")
    assert revision is not None
    assert revision.down_revision == "043_institution_outcomes"
    next_revision = script.get_revision("045_agentic_ai_platform")
    assert next_revision is not None
    assert next_revision.down_revision == "044_agent_execution_framework"
