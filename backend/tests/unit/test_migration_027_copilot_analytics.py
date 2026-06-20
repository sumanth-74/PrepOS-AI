from __future__ import annotations

from alembic.config import Config

from alembic.script import ScriptDirectory


def test_copilot_analytics_migration_exists_in_chain() -> None:
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revision = script.get_revision("027_copilot_analytics")
    assert revision is not None
    assert revision.down_revision == "026_mentor_effectiveness_learning"
