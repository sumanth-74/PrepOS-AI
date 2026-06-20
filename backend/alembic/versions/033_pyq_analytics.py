"""PYQ query analytics events (P7 S19)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "033_pyq_analytics"
down_revision = "032_pyq_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pyq_query_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=True),
        sa.Column("citation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.String(length=16), nullable=True),
        sa.Column("pyq_boost_applied", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pyq_retrieval_success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("concept_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_pyq_query_events_tenant_created",
        "pyq_query_events",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_pyq_query_events_tenant_created", table_name="pyq_query_events")
    op.drop_table("pyq_query_events")
