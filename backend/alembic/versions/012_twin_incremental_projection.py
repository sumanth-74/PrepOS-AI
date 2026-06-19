"""Twin S6.2: incremental projection, rebuild locks, and metrics."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "012_twin_incremental_projection"
down_revision = "011_twin_core_projection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "twin_rebuild_locks",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "student_id", "exam_id", name="pk_twin_rebuild_locks"),
    )
    op.create_index("ix_twin_rebuild_locks_expires_at", "twin_rebuild_locks", ["expires_at"])

    op.add_column(
        "preparation_twins",
        sa.Column("last_learning_graph_version", sa.Integer(), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column(
            "learning_graph_node_versions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("projection_revision", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("rebuild_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("skipped_rebuild_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("incremental_update_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("lock_contention_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("preparation_twins", "lock_contention_count")
    op.drop_column("preparation_twins", "incremental_update_count")
    op.drop_column("preparation_twins", "skipped_rebuild_count")
    op.drop_column("preparation_twins", "rebuild_count")
    op.drop_column("preparation_twins", "projection_revision")
    op.drop_column("preparation_twins", "learning_graph_node_versions")
    op.drop_column("preparation_twins", "last_learning_graph_version")
    op.drop_index("ix_twin_rebuild_locks_expires_at", table_name="twin_rebuild_locks")
    op.drop_table("twin_rebuild_locks")
