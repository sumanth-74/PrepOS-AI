"""PYQ intelligence catalog tables (P7 S19)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "032_pyq_intelligence"
down_revision = "031_current_affairs_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pyq_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("exam_stage", sa.String(length=32), nullable=False),
        sa.Column("paper", sa.String(length=64), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("source_reference", sa.String(length=256), nullable=True),
        sa.Column("difficulty", sa.Integer(), nullable=True),
        sa.Column("importance", sa.String(length=32), nullable=True),
        sa.Column(
            "knowledge_source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "knowledge_chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_chunks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_pyq_questions_exam_year_paper", "pyq_questions", ["exam_id", "year", "paper"])
    op.create_index("ix_pyq_questions_tenant_exam", "pyq_questions", ["tenant_id", "exam_id"])

    op.create_table(
        "pyq_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "pyq_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pyq_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("concept_id", sa.String(length=128), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=4, scale=3), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_pyq_mappings_pyq_id", "pyq_mappings", ["pyq_id"])
    op.create_index("ix_pyq_mappings_concept_id", "pyq_mappings", ["concept_id"])

    op.create_table(
        "pyq_statistics",
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=False),
        sa.Column("pyq_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_appearance_year", sa.Integer(), nullable=True),
        sa.Column("last_appearance_year", sa.Integer(), nullable=True),
        sa.Column("frequency_score", sa.Numeric(precision=6, scale=2), nullable=False, server_default="0"),
        sa.Column("trend_score", sa.Numeric(precision=6, scale=2), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("exam_id", "concept_id", name="pk_pyq_statistics"),
    )
    op.create_index("ix_pyq_statistics_exam_frequency", "pyq_statistics", ["exam_id", "frequency_score"])


def downgrade() -> None:
    op.drop_index("ix_pyq_statistics_exam_frequency", table_name="pyq_statistics")
    op.drop_table("pyq_statistics")
    op.drop_index("ix_pyq_mappings_concept_id", table_name="pyq_mappings")
    op.drop_index("ix_pyq_mappings_pyq_id", table_name="pyq_mappings")
    op.drop_table("pyq_mappings")
    op.drop_index("ix_pyq_questions_tenant_exam", table_name="pyq_questions")
    op.drop_index("ix_pyq_questions_exam_year_paper", table_name="pyq_questions")
    op.drop_table("pyq_questions")
