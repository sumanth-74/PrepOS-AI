"""Coaching memory for conversational context (P7 S23)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "037_coaching_memory"
down_revision = "036_recommendation_outcomes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "copilot_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("persona", sa.String(length=16), nullable=False),
        sa.Column("memory_type", sa.String(length=64), nullable=False),
        sa.Column("memory_key", sa.String(length=256), nullable=False),
        sa.Column("memory_value", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_copilot_memories_user_persona", "copilot_memories", ["user_id", "persona"])
    op.create_index("ix_copilot_memories_memory_type", "copilot_memories", ["memory_type"])
    op.create_index("ix_copilot_memories_tenant_id", "copilot_memories", ["tenant_id"])
    op.create_unique_constraint(
        "uq_copilot_memories_tenant_user_key",
        "copilot_memories",
        ["tenant_id", "user_id", "memory_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_copilot_memories_tenant_user_key", "copilot_memories", type_="unique")
    op.drop_index("ix_copilot_memories_tenant_id", table_name="copilot_memories")
    op.drop_index("ix_copilot_memories_memory_type", table_name="copilot_memories")
    op.drop_index("ix_copilot_memories_user_persona", table_name="copilot_memories")
    op.drop_table("copilot_memories")
