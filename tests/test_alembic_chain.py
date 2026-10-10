"""
Review 2026-09-25 (low): alembic 001 had no revision id, which broke the chain,
and alembic.ini had options outside any [section], so configparser refused it.

These checks only read the migration scripts; no database is touched.
"""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parent.parent


def _script_dir() -> ScriptDirectory:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    return ScriptDirectory.from_config(cfg)


def test_alembic_ini_parses_with_script_location():
    cfg = Config(str(ROOT / "alembic.ini"))
    assert cfg.get_main_option("script_location") == "alembic"


def test_migration_chain_is_linear_from_001():
    script = _script_dir()
    assert script.get_heads() == ["005"]
    assert script.get_bases() == ["001"]
    revisions = [rev.revision for rev in script.walk_revisions()]  # head -> base
    assert revisions == ["005", "004", "003", "002", "001"]
    for rev in script.walk_revisions():
        expected_down = None if rev.revision == "001" else f"{int(rev.revision) - 1:03d}"
        assert rev.down_revision == expected_down
