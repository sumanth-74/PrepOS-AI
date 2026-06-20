"""Institutional intelligence and executive decision engine (P7 S28)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "042_institution_intelligence"
down_revision = "041_cohort_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institution_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("insight_type", sa.String(length=64), nullable=False),
        sa.Column("insight_key", sa.String(length=128), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("calculation_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source_metrics_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_institution_insights_tenant_type",
        "institution_insights",
        ["tenant_id", "insight_type"],
    )
    op.create_index("ix_institution_insights_created", "institution_insights", ["created_at"])

    op.create_table(
        "institution_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("expected_impact", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("affected_students", sa.Integer(), nullable=False),
        sa.Column("affected_cohorts_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("priority_score", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_institution_recommendations_tenant",
        "institution_recommendations",
        ["tenant_id", "priority_score"],
    )

    op.create_table(
        "institution_trends",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trend_type", sa.String(length=64), nullable=False),
        sa.Column("trend_key", sa.String(length=128), nullable=False),
        sa.Column("trend_direction", sa.String(length=16), nullable=False),
        sa.Column("delta_value", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("period", sa.String(length=16), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_institution_trends_tenant_type",
        "institution_trends",
        ["tenant_id", "trend_type"],
    )

    op.create_table(
        "institution_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_institution_events_tenant_created",
        "institution_events",
        ["tenant_id", "created_at"],
    )
    op.create_index("ix_institution_events_type", "institution_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_institution_events_type", table_name="institution_events")
    op.drop_index("ix_institution_events_tenant_created", table_name="institution_events")
    op.drop_table("institution_events")
    op.drop_index("ix_institution_trends_tenant_type", table_name="institution_trends")
    op.drop_table("institution_trends")
    op.drop_index("ix_institution_recommendations_tenant", table_name="institution_recommendations")
    op.drop_table("institution_recommendations")
    op.drop_index("ix_institution_insights_created", table_name="institution_insights")
    op.drop_index("ix_institution_insights_tenant_type", table_name="institution_insights")
    op.drop_table("institution_insights")
