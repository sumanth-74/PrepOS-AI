"""Mentor effectiveness learning S8.3."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "026_mentor_effectiveness_learning"
down_revision = "025_mentor_case_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mentor_action_effectiveness",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("effectiveness_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("readiness_delta", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("predicted_score_delta", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("success_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "action_type"),
    )
    op.create_index(
        "ix_mentor_action_effectiveness_tenant_score",
        "mentor_action_effectiveness",
        ["tenant_id", "effectiveness_score"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_mentor_action_effectiveness_tenant_score",
        table_name="mentor_action_effectiveness",
    )
    op.drop_table("mentor_action_effectiveness")
