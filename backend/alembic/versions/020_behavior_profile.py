"""Behavior profile S7.3."""

from alembic import op
import sqlalchemy as sa

revision = "020_behavior_profile"
down_revision = "019_intervention_outcomes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preparation_twins",
        sa.Column("learning_style", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("risk_profile", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("consistency_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("discipline_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("engagement_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("preparation_twins", "engagement_score")
    op.drop_column("preparation_twins", "discipline_score")
    op.drop_column("preparation_twins", "consistency_score")
    op.drop_column("preparation_twins", "risk_profile")
    op.drop_column("preparation_twins", "learning_style")
