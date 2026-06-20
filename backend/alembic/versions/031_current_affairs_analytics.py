"""Current affairs query analytics events (P7 S18)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "031_current_affairs_analytics"
down_revision = "030_current_affairs_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "current_affairs_query_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("citation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.String(length=16), nullable=True),
        sa.Column("recency_boost_applied", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("recency_retrieval_success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_ca_query_events_tenant_created",
        "current_affairs_query_events",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ca_query_events_tenant_created", table_name="current_affairs_query_events")
    op.drop_table("current_affairs_query_events")
