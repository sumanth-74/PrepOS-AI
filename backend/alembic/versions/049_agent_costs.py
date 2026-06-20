"""Cost and performance intelligence (P10 S39)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "049_agent_costs"
down_revision = "048_agent_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_costs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_type", sa.String(length=64), nullable=False),
        sa.Column("workflow_type", sa.String(length=64), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=False),
        sa.Column("tokens_out", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_costs_tenant_created", "agent_costs", ["tenant_id", "created_at"])
    op.create_index("ix_agent_costs_agent", "agent_costs", ["agent_type"])


def downgrade() -> None:
    op.drop_index("ix_agent_costs_agent", table_name="agent_costs")
    op.drop_index("ix_agent_costs_tenant_created", table_name="agent_costs")
    op.drop_table("agent_costs")
