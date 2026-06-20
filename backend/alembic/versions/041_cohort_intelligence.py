"""Cohort intelligence and student segmentation (P7 S27)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "041_cohort_intelligence"
down_revision = "040_mentor_interventions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cohort_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohort_id", sa.String(length=128), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("student_count", sa.Integer(), nullable=False),
        sa.Column("avg_readiness", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("avg_forecast", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("avg_effectiveness", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("risk_count", sa.Integer(), nullable=False),
        sa.Column("segment_counts_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cohort_snapshots_tenant_cohort", "cohort_snapshots", ["tenant_id", "cohort_id"])
    op.create_index("ix_cohort_snapshots_created", "cohort_snapshots", ["created_at"])

    op.create_table(
        "student_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohort_id", sa.String(length=128), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("segment_type", sa.String(length=64), nullable=False),
        sa.Column("segment_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("risk_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_segments_tenant_cohort", "student_segments", ["tenant_id", "cohort_id"])
    op.create_index("ix_student_segments_student", "student_segments", ["student_id", "calculated_at"])

    op.create_table(
        "cohort_trends",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohort_id", sa.String(length=128), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=False),
        sa.Column("trend_direction", sa.String(length=16), nullable=False),
        sa.Column("readiness_delta", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("period", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cohort_trends_tenant_cohort", "cohort_trends", ["tenant_id", "cohort_id"])

    op.create_table(
        "cohort_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohort_id", sa.String(length=128), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cohort_events_tenant_created", "cohort_events", ["tenant_id", "created_at"])
    op.create_index("ix_cohort_events_type", "cohort_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_cohort_events_type", table_name="cohort_events")
    op.drop_index("ix_cohort_events_tenant_created", table_name="cohort_events")
    op.drop_table("cohort_events")
    op.drop_index("ix_cohort_trends_tenant_cohort", table_name="cohort_trends")
    op.drop_table("cohort_trends")
    op.drop_index("ix_student_segments_student", table_name="student_segments")
    op.drop_index("ix_student_segments_tenant_cohort", table_name="student_segments")
    op.drop_table("student_segments")
    op.drop_index("ix_cohort_snapshots_created", table_name="cohort_snapshots")
    op.drop_index("ix_cohort_snapshots_tenant_cohort", table_name="cohort_snapshots")
    op.drop_table("cohort_snapshots")
