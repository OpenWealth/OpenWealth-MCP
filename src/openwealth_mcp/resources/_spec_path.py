"""Shared helper for resolving vendored OpenAPI spec files."""

from __future__ import annotations

from pathlib import Path


def resolve_spec_path(filename: str) -> Path | None:
    """Return the first existing path candidate for a vendored OpenAPI spec.

    Searches three locations in order:
    1. Inside the installed wheel (force-included under ``openwealth_mcp/specs/``).
    2. The repo root ``specs/`` directory when the package is installed in editable mode.
    3. ``specs/`` relative to the current working directory (fallback).
    """
    here = Path(__file__).resolve()
    package_root = here.parents[1]  # .../openwealth_mcp
    candidates = [
        package_root / "specs" / filename,  # wheel force-include
        here.parents[3] / "specs" / filename,  # editable: repo root / specs
        Path.cwd() / "specs" / filename,
    ]
    return next((p for p in candidates if p.is_file()), None)
