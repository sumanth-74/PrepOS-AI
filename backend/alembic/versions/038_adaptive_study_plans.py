"""Adaptive study plans and planning analytics (P7 S24)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "038_adaptive_study_plans"
down_revision = "037_coaching_memory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "study_plan_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=False),
        sa.Column("readiness_snapshot", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("forecast_snapshot", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_study_plan_versions_tenant_user", "study_plan_versions", ["tenant_id", "user_id"])
    op.create_index("ix_study_plan_versions_student_status", "study_plan_versions", ["student_id", "status"])

    op.create_table(
        "study_plan_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("study_plan_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=False),
        sa.Column("activity_type", sa.String(length=64), nullable=False),
        sa.Column("priority_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("estimated_readiness_gain", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("source_reason", sa.String(length=512), nullable=False),
        sa.Column("completion_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_study_plan_items_plan_date", "study_plan_items", ["plan_id", "scheduled_date"])
    op.create_index("ix_study_plan_items_concept", "study_plan_items", ["concept_id"])

    op.create_table(
        "study_plan_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("study_plan_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=False),
        sa.Column("revision_reason", sa.String(length=256), nullable=False),
        sa.Column("old_priority", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("new_priority", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_study_plan_revisions_plan", "study_plan_revisions", ["plan_id"])

    op.create_table(
        "planning_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("concept_id", sa.String(length=128), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("priority_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("estimated_gain", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_planning_events_tenant_created", "planning_events", ["tenant_id", "created_at"])
    op.create_index("ix_planning_events_type", "planning_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_planning_events_type", table_name="planning_events")
    op.drop_index("ix_planning_events_tenant_created", table_name="planning_events")
    op.drop_table("planning_events")
    op.drop_index("ix_study_plan_revisions_plan", table_name="study_plan_revisions")
    op.drop_table("study_plan_revisions")
    op.drop_index("ix_study_plan_items_concept", table_name="study_plan_items")
    op.drop_index("ix_study_plan_items_plan_date", table_name="study_plan_items")
    op.drop_table("study_plan_items")
    op.drop_index("ix_study_plan_versions_student_status", table_name="study_plan_versions")
    op.drop_index("ix_study_plan_versions_tenant_user", table_name="study_plan_versions")
    op.drop_table("study_plan_versions")
