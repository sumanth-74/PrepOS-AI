"""Copilot analytics R0.2."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "027_copilot_analytics"
down_revision = "026_mentor_effectiveness_learning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "copilot_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("persona", sa.String(length=32), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("query_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_copilot_sessions_tenant_user", "copilot_sessions", ["tenant_id", "user_id"])
    op.create_index(
        "ix_copilot_sessions_tenant_last_activity",
        "copilot_sessions",
        ["tenant_id", "last_activity_at"],
    )

    op.create_table(
        "copilot_queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("persona", sa.String(length=32), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["copilot_sessions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_copilot_queries_tenant_created", "copilot_queries", ["tenant_id", "created_at"])
    op.create_index("ix_copilot_queries_tenant_intent", "copilot_queries", ["tenant_id", "intent"])
    op.create_index("ix_copilot_queries_tenant_persona", "copilot_queries", ["tenant_id", "persona"])
    op.create_index("ix_copilot_queries_session_id", "copilot_queries", ["session_id"])

    op.create_table(
        "copilot_intent_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("persona", sa.String(length=32), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=False),
        sa.Column("query_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "metric_date",
            "persona",
            "intent",
            name="uq_copilot_intent_metrics_daily",
        ),
    )
    op.create_index(
        "ix_copilot_intent_metrics_tenant_date",
        "copilot_intent_metrics",
        ["tenant_id", "metric_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_copilot_intent_metrics_tenant_date", table_name="copilot_intent_metrics")
    op.drop_table("copilot_intent_metrics")
    op.drop_index("ix_copilot_queries_session_id", table_name="copilot_queries")
    op.drop_index("ix_copilot_queries_tenant_persona", table_name="copilot_queries")
    op.drop_index("ix_copilot_queries_tenant_intent", table_name="copilot_queries")
    op.drop_index("ix_copilot_queries_tenant_created", table_name="copilot_queries")
    op.drop_table("copilot_queries")
    op.drop_index("ix_copilot_sessions_tenant_last_activity", table_name="copilot_sessions")
    op.drop_index("ix_copilot_sessions_tenant_user", table_name="copilot_sessions")
    op.drop_table("copilot_sessions")
