from __future__ import annotations

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_coaching_memory_migration_exists_in_chain() -> None:
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revision = script.get_revision("037_coaching_memory")
    assert revision is not None
    assert revision.down_revision == "036_recommendation_outcomes"
