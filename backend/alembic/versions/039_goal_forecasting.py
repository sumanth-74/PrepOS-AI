"""Goal forecasting and readiness simulation (P7 S25)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "039_goal_forecasting"
down_revision = "038_adaptive_study_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goal_forecasts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("current_readiness", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("projected_readiness", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("target_readiness", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("probability_of_success", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("forecast_status", sa.String(length=32), nullable=False),
        sa.Column("top_drivers_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_goal_forecasts_tenant_user", "goal_forecasts", ["tenant_id", "user_id"])
    op.create_index("ix_goal_forecasts_student_created", "goal_forecasts", ["student_id", "created_at"])

    op.create_table(
        "forecast_scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("forecast_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("goal_forecasts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_type", sa.String(length=64), nullable=False),
        sa.Column("scenario_name", sa.String(length=128), nullable=False),
        sa.Column("weekly_minutes", sa.Integer(), nullable=False),
        sa.Column("projected_readiness", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("projected_score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("probability_of_success", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_forecast_scenarios_forecast", "forecast_scenarios", ["forecast_id"])

    op.create_table(
        "forecast_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("forecast_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_forecast_events_tenant_created", "forecast_events", ["tenant_id", "created_at"])
    op.create_index("ix_forecast_events_type", "forecast_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_forecast_events_type", table_name="forecast_events")
    op.drop_index("ix_forecast_events_tenant_created", table_name="forecast_events")
    op.drop_table("forecast_events")
    op.drop_index("ix_forecast_scenarios_forecast", table_name="forecast_scenarios")
    op.drop_table("forecast_scenarios")
    op.drop_index("ix_goal_forecasts_student_created", table_name="goal_forecasts")
    op.drop_index("ix_goal_forecasts_tenant_user", table_name="goal_forecasts")
    op.drop_table("goal_forecasts")
