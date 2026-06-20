"""Recommendation outcomes and effectiveness rollups (P7 S22)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "036_recommendation_outcomes"
down_revision = "035_recommendation_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recommendation_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("recommendation_event_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("concept_id", sa.String(length=128), nullable=False),
        sa.Column("readiness_before", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("readiness_after", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("forecast_before", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("forecast_after", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("weakness_before", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("weakness_after", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("study_minutes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("predicted_gain", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("actual_gain", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("effectiveness_score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_recommendation_outcomes_user_created",
        "recommendation_outcomes",
        ["user_id", "created_at"],
    )
    op.create_index("ix_recommendation_outcomes_concept_id", "recommendation_outcomes", ["concept_id"])
    op.create_index("ix_recommendation_outcomes_tenant_id", "recommendation_outcomes", ["tenant_id"])

    op.create_table(
        "recommendation_effectiveness_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=False),
        sa.Column("recommendation_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("completion_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("average_predicted_gain", sa.Numeric(precision=6, scale=2), nullable=False, server_default=sa.text("0")),
        sa.Column("average_actual_gain", sa.Numeric(precision=6, scale=2), nullable=False, server_default=sa.text("0")),
        sa.Column("average_effectiveness", sa.Numeric(precision=6, scale=2), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_recommendation_effectiveness_metrics_tenant_date",
        "recommendation_effectiveness_metrics",
        ["tenant_id", "metric_date"],
    )
    op.create_unique_constraint(
        "uq_recommendation_effectiveness_metrics_tenant_date_concept",
        "recommendation_effectiveness_metrics",
        ["tenant_id", "metric_date", "concept_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_recommendation_effectiveness_metrics_tenant_date_concept",
        "recommendation_effectiveness_metrics",
        type_="unique",
    )
    op.drop_index("ix_recommendation_effectiveness_metrics_tenant_date", table_name="recommendation_effectiveness_metrics")
    op.drop_table("recommendation_effectiveness_metrics")
    op.drop_index("ix_recommendation_outcomes_tenant_id", table_name="recommendation_outcomes")
    op.drop_index("ix_recommendation_outcomes_concept_id", table_name="recommendation_outcomes")
    op.drop_index("ix_recommendation_outcomes_user_created", table_name="recommendation_outcomes")
    op.drop_table("recommendation_outcomes")
