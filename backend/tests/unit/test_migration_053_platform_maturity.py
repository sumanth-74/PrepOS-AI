"""Migration 053 platform maturity head check."""

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_platform_maturity_migration_is_head() -> None:
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    assert script.get_current_head() == "053_platform_maturity"
