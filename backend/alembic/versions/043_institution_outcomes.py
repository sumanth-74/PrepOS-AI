"""Institutional outcome intelligence and ROI engine (P7 S29)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "043_institution_outcomes"
down_revision = "042_institution_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institution_initiatives",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("initiative_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("affected_students", sa.Integer(), nullable=False),
        sa.Column("affected_cohorts_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("expected_outcomes_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("actual_outcomes_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("before_state_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_institution_initiatives_tenant_status",
        "institution_initiatives",
        ["tenant_id", "status"],
    )

    op.create_table(
        "institution_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("initiative_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome_type", sa.String(length=64), nullable=False),
        sa.Column("subject_key", sa.String(length=128), nullable=False),
        sa.Column("before_readiness", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("after_readiness", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("before_forecast", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("after_forecast", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("before_cohort_health", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("after_cohort_health", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("before_risk_count", sa.Integer(), nullable=False),
        sa.Column("after_risk_count", sa.Integer(), nullable=False),
        sa.Column("actual_gain", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("expected_gain", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("variance", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_institution_outcomes_tenant_initiative",
        "institution_outcomes",
        ["tenant_id", "initiative_id"],
    )

    op.create_table(
        "institution_roi_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("initiative_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject_key", sa.String(length=128), nullable=False),
        sa.Column("roi_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("readiness_gain", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("forecast_gain", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("cohort_health_gain", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("risk_reduction", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("calculation_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_institution_roi_metrics_tenant_score",
        "institution_roi_metrics",
        ["tenant_id", "roi_score"],
    )

    op.create_table(
        "institution_initiative_effectiveness",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("initiative_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("effectiveness_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("readiness_delta", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("forecast_delta", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("cohort_health_delta", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("risk_reduction", sa.Integer(), nullable=False),
        sa.Column("roi_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("calculation_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_institution_initiative_effectiveness_initiative",
        "institution_initiative_effectiveness",
        ["tenant_id", "initiative_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_institution_initiative_effectiveness_initiative",
        table_name="institution_initiative_effectiveness",
    )
    op.drop_table("institution_initiative_effectiveness")
    op.drop_index("ix_institution_roi_metrics_tenant_score", table_name="institution_roi_metrics")
    op.drop_table("institution_roi_metrics")
    op.drop_index("ix_institution_outcomes_tenant_initiative", table_name="institution_outcomes")
    op.drop_table("institution_outcomes")
    op.drop_index("ix_institution_initiatives_tenant_status", table_name="institution_initiatives")
    op.drop_table("institution_initiatives")
