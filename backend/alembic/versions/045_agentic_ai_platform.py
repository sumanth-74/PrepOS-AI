"""P9 agentic AI platform: critique, reflection, execution graph, learning signals."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "045_agentic_ai_platform"
down_revision = "044_agent_execution_framework"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_critiques",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("unsupported_claims", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("citation_issues", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("critique_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_critiques_execution", "agent_critiques", ["execution_id"])
    op.create_index("ix_agent_critiques_tenant_created", "agent_critiques", ["tenant_id", "created_at"])

    op.create_table(
        "agent_reflections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("critique_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_answer", sa.Text(), nullable=False),
        sa.Column("refined_answer", sa.Text(), nullable=False),
        sa.Column("improvements_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_reflections_execution", "agent_reflections", ["execution_id"])

    op.create_table(
        "agent_execution_graph_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_id", sa.String(length=64), nullable=False),
        sa.Column("parent_node_id", sa.String(length=64), nullable=True),
        sa.Column("agent_type", sa.String(length=64), nullable=False),
        sa.Column("tool_name", sa.String(length=64), nullable=True),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_graph_execution", "agent_execution_graph_nodes", ["execution_id"])
    op.create_index("ix_agent_graph_tenant", "agent_execution_graph_nodes", ["tenant_id"])

    op.create_table(
        "agent_learning_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal_type", sa.String(length=64), nullable=False),
        sa.Column("subject_key", sa.String(length=128), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=True),
        sa.Column("effectiveness_score", sa.Float(), nullable=False),
        sa.Column("signal_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_learning_signals_tenant_type", "agent_learning_signals", ["tenant_id", "signal_type"])


def downgrade() -> None:
    op.drop_index("ix_agent_learning_signals_tenant_type", table_name="agent_learning_signals")
    op.drop_table("agent_learning_signals")
    op.drop_index("ix_agent_graph_tenant", table_name="agent_execution_graph_nodes")
    op.drop_index("ix_agent_graph_execution", table_name="agent_execution_graph_nodes")
    op.drop_table("agent_execution_graph_nodes")
    op.drop_index("ix_agent_reflections_execution", table_name="agent_reflections")
    op.drop_table("agent_reflections")
    op.drop_index("ix_agent_critiques_tenant_created", table_name="agent_critiques")
    op.drop_index("ix_agent_critiques_execution", table_name="agent_critiques")
    op.drop_table("agent_critiques")
