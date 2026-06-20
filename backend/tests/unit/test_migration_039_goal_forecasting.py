from __future__ import annotations

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_goal_forecasting_migration_chain() -> None:
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    revision = script.get_revision("039_goal_forecasting")
    assert revision is not None
    assert revision.down_revision == "038_adaptive_study_plans"
