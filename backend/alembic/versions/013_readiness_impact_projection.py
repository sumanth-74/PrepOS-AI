"""Twin S6.3: readiness impact on recommendations."""

from alembic import op
import sqlalchemy as sa

revision = "013_readiness_impact_projection"
down_revision = "012_twin_incremental_projection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preparation_twin_recommendations",
        sa.Column(
            "readiness_gain",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="0.00",
        ),
    )


def downgrade() -> None:
    op.drop_column("preparation_twin_recommendations", "readiness_gain")
