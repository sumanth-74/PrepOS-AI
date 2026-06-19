"""Twin S5.4: persisted recommendation rows for analytics."""

from alembic import op
import sqlalchemy as sa

revision = "008_twin_recommendations"
down_revision = "007_retention_state_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "preparation_twin_recommendations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=False),
        sa.Column("recommendation_type", sa.String(length=64), nullable=False),
        sa.Column("recommendation_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "student_id",
            "exam_id",
            "concept_id",
            name="uq_preparation_twin_recommendations_student_exam_concept",
        ),
    )
    op.create_index(
        "ix_preparation_twin_recommendations_tenant_id",
        "preparation_twin_recommendations",
        ["tenant_id"],
    )
    op.create_index(
        "ix_preparation_twin_recommendations_student_id",
        "preparation_twin_recommendations",
        ["student_id"],
    )
    op.create_index(
        "ix_preparation_twin_recommendations_exam_id",
        "preparation_twin_recommendations",
        ["exam_id"],
    )
    op.create_index(
        "ix_preparation_twin_recommendations_concept_id",
        "preparation_twin_recommendations",
        ["concept_id"],
    )
    op.create_index(
        "ix_preparation_twin_recommendations_created_at",
        "preparation_twin_recommendations",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_preparation_twin_recommendations_created_at",
        table_name="preparation_twin_recommendations",
    )
    op.drop_index(
        "ix_preparation_twin_recommendations_concept_id",
        table_name="preparation_twin_recommendations",
    )
    op.drop_index(
        "ix_preparation_twin_recommendations_exam_id",
        table_name="preparation_twin_recommendations",
    )
    op.drop_index(
        "ix_preparation_twin_recommendations_student_id",
        table_name="preparation_twin_recommendations",
    )
    op.drop_index(
        "ix_preparation_twin_recommendations_tenant_id",
        table_name="preparation_twin_recommendations",
    )
    op.drop_table("preparation_twin_recommendations")
