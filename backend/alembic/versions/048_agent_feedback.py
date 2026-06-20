"""Human feedback loop (P10 S38)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "048_agent_feedback"
down_revision = "047_agent_evaluation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.String(length=32), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("agent_type", sa.String(length=64), nullable=True),
        sa.Column("intent", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_feedback_tenant_created", "agent_feedback", ["tenant_id", "created_at"])
    op.create_index("ix_agent_feedback_trace", "agent_feedback", ["trace_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_feedback_trace", table_name="agent_feedback")
    op.drop_index("ix_agent_feedback_tenant_created", table_name="agent_feedback")
    op.drop_table("agent_feedback")
