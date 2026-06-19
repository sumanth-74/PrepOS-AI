"""Twin S6.0: canonical profile columns and twin_payload on preparation_twins."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "011_twin_core_projection"
down_revision = "010_twin_projection_snapshot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preparation_twins",
        sa.Column("profile_version", sa.String(length=32), nullable=False, server_default="TWIN_PROFILE_V1"),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("recommendation_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("last_recommendation_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column(
            "twin_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column(
        "preparation_twins",
        "largest_positive_driver",
        existing_type=sa.String(length=32),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
    op.alter_column(
        "preparation_twins",
        "largest_negative_driver",
        existing_type=sa.String(length=32),
        type_=sa.String(length=64),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "preparation_twins",
        "largest_negative_driver",
        existing_type=sa.String(length=64),
        type_=sa.String(length=32),
        existing_nullable=True,
    )
    op.alter_column(
        "preparation_twins",
        "largest_positive_driver",
        existing_type=sa.String(length=64),
        type_=sa.String(length=32),
        existing_nullable=True,
    )
    op.drop_column("preparation_twins", "twin_payload")
    op.drop_column("preparation_twins", "last_recommendation_at")
    op.drop_column("preparation_twins", "recommendation_count")
    op.drop_column("preparation_twins", "profile_version")
