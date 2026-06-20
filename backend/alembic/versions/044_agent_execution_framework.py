"""Agent execution framework and orchestration audit trail (P8)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "044_agent_execution_framework"
down_revision = "043_institution_outcomes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.String(length=64), nullable=False),
        sa.Column("persona", sa.String(length=16), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("plan_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("results_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("execution_time_ms", sa.Integer(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_executions_tenant_created", "agent_executions", ["tenant_id", "created_at"])
    op.create_index("ix_agent_executions_agent_type", "agent_executions", ["agent_type"])

    op.create_table(
        "agent_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("persona", sa.String(length=16), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_tasks_execution", "agent_tasks", ["execution_id"])

    op.create_table(
        "agent_workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("trigger_event", sa.String(length=64), nullable=False),
        sa.Column("subject_key", sa.String(length=128), nullable=False),
        sa.Column("plan_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("results_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agent_workflows_tenant_type", "agent_workflows", ["tenant_id", "workflow_type"])

    op.create_table(
        "agent_workflow_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_agent_workflow_events_tenant_created",
        "agent_workflow_events",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_workflow_events_tenant_created", table_name="agent_workflow_events")
    op.drop_table("agent_workflow_events")
    op.drop_index("ix_agent_workflows_tenant_type", table_name="agent_workflows")
    op.drop_table("agent_workflows")
    op.drop_index("ix_agent_tasks_execution", table_name="agent_tasks")
    op.drop_table("agent_tasks")
    op.drop_index("ix_agent_executions_agent_type", table_name="agent_executions")
    op.drop_index("ix_agent_executions_tenant_created", table_name="agent_executions")
    op.drop_table("agent_executions")
