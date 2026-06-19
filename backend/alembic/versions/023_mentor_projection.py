"""Mentor projection S8.0."""

from alembic import op
import sqlalchemy as sa

revision = "023_mentor_projection"
down_revision = "021_personalization_projection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preparation_twins",
        sa.Column("mentor_status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("top_mentor_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("preparation_twins", "top_mentor_message")
    op.drop_column("preparation_twins", "mentor_status")
