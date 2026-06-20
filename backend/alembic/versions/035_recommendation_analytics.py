"""Recommendation analytics events (P7 S21)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "035_recommendation_analytics"
down_revision = "034_rag_quality"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recommendation_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=True),
        sa.Column("impact_score", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("estimated_gain", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("readiness_gain_after", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_recommendation_events_tenant_created",
        "recommendation_events",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_recommendation_events_tenant_created", table_name="recommendation_events")
    op.drop_table("recommendation_events")
