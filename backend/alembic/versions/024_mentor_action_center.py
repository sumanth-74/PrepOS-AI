"""Mentor action center S8.1."""

from alembic import op
import sqlalchemy as sa

revision = "024_mentor_action_center"
down_revision = "023_mentor_projection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preparation_twins",
        sa.Column("mentor_action_type", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("mentor_action_priority", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("escalation_level", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("preparation_twins", "escalation_level")
    op.drop_column("preparation_twins", "mentor_action_priority")
    op.drop_column("preparation_twins", "mentor_action_type")
