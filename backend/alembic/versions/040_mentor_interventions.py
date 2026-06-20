"""Mentor intervention optimization (P7 S26)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "040_mentor_interventions"
down_revision = "039_goal_forecasting"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mentor_interventions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mentor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("intervention_type", sa.String(length=64), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("predicted_gain", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("priority_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_mentor_interventions_tenant_student",
        "mentor_interventions",
        ["tenant_id", "student_id"],
    )
    op.create_index(
        "ix_mentor_interventions_mentor_status",
        "mentor_interventions",
        ["mentor_id", "status"],
    )

    op.create_table(
        "intervention_effectiveness",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "intervention_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mentor_interventions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("readiness_before", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("readiness_after", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("actual_gain", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("effectiveness_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_intervention_effectiveness_intervention",
        "intervention_effectiveness",
        ["intervention_id"],
    )

    op.create_table(
        "intervention_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("intervention_type", sa.String(length=64), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=True),
        sa.Column("recommendation_reason", sa.Text(), nullable=False),
        sa.Column("impact_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("predicted_gain", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_intervention_recommendations_student_created",
        "intervention_recommendations",
        ["student_id", "created_at"],
    )
    op.create_index(
        "ix_intervention_recommendations_tenant_created",
        "intervention_recommendations",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_intervention_recommendations_tenant_created", table_name="intervention_recommendations")
    op.drop_index("ix_intervention_recommendations_student_created", table_name="intervention_recommendations")
    op.drop_table("intervention_recommendations")
    op.drop_index("ix_intervention_effectiveness_intervention", table_name="intervention_effectiveness")
    op.drop_table("intervention_effectiveness")
    op.drop_index("ix_mentor_interventions_mentor_status", table_name="mentor_interventions")
    op.drop_index("ix_mentor_interventions_tenant_student", table_name="mentor_interventions")
    op.drop_table("mentor_interventions")
