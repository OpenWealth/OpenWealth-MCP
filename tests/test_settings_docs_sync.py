"""Assert that the README configuration table matches Settings field-by-field.

This prevents the silent drift introduced by extra="ignore": a user who
follows a README that documents a non-existent variable gets no error, only
a no-op.  This test makes the documentation diverge loudly.
"""

from __future__ import annotations

import re
from pathlib import Path

from openwealth_mcp.config import Settings

_README = Path(__file__).parents[1] / "README.md"

# Matches table rows like: | `OPENWEALTH_FOO` | ... |
_TABLE_ROW_RE = re.compile(r"\|\s*`(OPENWEALTH_[A-Z0-9_]+)`\s*\|")


def _readme_vars() -> set[str]:
    """Return all OPENWEALTH_* variable names in the README config table."""
    text = _README.read_text(encoding="utf-8")
    # Only scan lines after the "## Configuration" heading.
    config_section = re.split(r"^## Configuration", text, maxsplit=1, flags=re.MULTILINE)
    if len(config_section) < 2:
        return set()
    section = config_section[1]
    # Stop at the next ## heading.
    next_section = re.split(r"^## ", section, maxsplit=1, flags=re.MULTILINE)
    table_text = next_section[0]
    return {m.group(1) for m in _TABLE_ROW_RE.finditer(table_text)}


def _settings_vars() -> set[str]:
    """Return all OPENWEALTH_* env-var names from Settings fields."""
    prefix = Settings.model_config.get("env_prefix", "OPENWEALTH_")
    return {f"{prefix}{name.upper()}" for name in Settings.model_fields}


def test_readme_config_table_matches_settings() -> None:
    """Every env-var in the README config table must exist in Settings."""
    readme = _readme_vars()
    settings = _settings_vars()

    unknown = readme - settings
    assert not unknown, (
        f"README documents variables that do not exist in Settings: {sorted(unknown)}\n"
        "Update the README config table or add the variable to Settings."
    )


def test_settings_vars_all_documented() -> None:
    """Every Settings field must appear in the README config table."""
    readme = _readme_vars()
    settings = _settings_vars()

    undocumented = settings - readme
    assert not undocumented, (
        f"Settings fields not documented in README config table: {sorted(undocumented)}\n"
        "Add each variable to the ## Configuration table in README.md."
    )
