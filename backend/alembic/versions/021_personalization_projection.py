"""Personalization projection S7.4."""

from alembic import op
import sqlalchemy as sa

revision = "021_personalization_projection"
down_revision = "020_behavior_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preparation_twins",
        sa.Column("best_activity_type", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("top_multiplier", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("historical_effectiveness", sa.Numeric(precision=5, scale=2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("preparation_twins", "historical_effectiveness")
    op.drop_column("preparation_twins", "top_multiplier")
    op.drop_column("preparation_twins", "best_activity_type")
