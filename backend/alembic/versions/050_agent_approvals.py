"""Approval workflows (P10 S40)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "050_agent_approvals"
down_revision = "049_agent_costs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("proposed_by_agent", sa.String(length=64), nullable=False),
        sa.Column("subject_key", sa.String(length=128), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_pending_actions_tenant_status", "pending_actions", ["tenant_id", "status"])
    op.create_index("ix_pending_actions_subject", "pending_actions", ["subject_key"])


def downgrade() -> None:
    op.drop_index("ix_pending_actions_subject", table_name="pending_actions")
    op.drop_index("ix_pending_actions_tenant_status", table_name="pending_actions")
    op.drop_table("pending_actions")
