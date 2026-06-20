"""Agent evaluation platform (P10 S37)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "047_agent_evaluation"
down_revision = "046_agent_traces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("retrieval_score", sa.Float(), nullable=False),
        sa.Column("citation_score", sa.Float(), nullable=False),
        sa.Column("hallucination_score", sa.Float(), nullable=False),
        sa.Column("support_score", sa.Float(), nullable=False),
        sa.Column("answer_quality_score", sa.Float(), nullable=False),
        sa.Column("planner_quality_score", sa.Float(), nullable=False),
        sa.Column("evaluation_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_evaluations_tenant", "agent_evaluations", ["tenant_id", "created_at"])
    op.create_index("ix_agent_evaluations_trace", "agent_evaluations", ["trace_id"])

    op.create_table(
        "agent_benchmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("benchmark_name", sa.String(length=128), nullable=False),
        sa.Column("suite_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("scenario_count", sa.Integer(), nullable=False),
        sa.Column("passed_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("results_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agent_benchmarks_suite", "agent_benchmarks", ["suite_type", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_agent_benchmarks_suite", table_name="agent_benchmarks")
    op.drop_table("agent_benchmarks")
    op.drop_index("ix_agent_evaluations_trace", table_name="agent_evaluations")
    op.drop_index("ix_agent_evaluations_tenant", table_name="agent_evaluations")
    op.drop_table("agent_evaluations")
