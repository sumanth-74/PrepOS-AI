"""Study plan S6.4 projection."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "014_study_plan_projection"
down_revision = "013_readiness_impact_projection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_study_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("daily_plan_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("weekly_plan_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("total_estimated_gain", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "student_id",
            "exam_id",
            name="uq_student_study_plans_tenant_student_exam",
        ),
    )
    op.create_index("ix_student_study_plans_tenant_id", "student_study_plans", ["tenant_id"])
    op.create_index("ix_student_study_plans_student_id", "student_study_plans", ["student_id"])
    op.create_index("ix_student_study_plans_exam_id", "student_study_plans", ["exam_id"])
    op.create_index("ix_student_study_plans_generated_at", "student_study_plans", ["generated_at"])


def downgrade() -> None:
    op.drop_index("ix_student_study_plans_generated_at", table_name="student_study_plans")
    op.drop_index("ix_student_study_plans_exam_id", table_name="student_study_plans")
    op.drop_index("ix_student_study_plans_student_id", table_name="student_study_plans")
    op.drop_index("ix_student_study_plans_tenant_id", table_name="student_study_plans")
    op.drop_table("student_study_plans")
