"""Input validation helpers shared by Custody and Trading tool adapters."""

from __future__ import annotations

import re

from openwealth_mcp.errors import ToolValidationError

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MAX_LIMIT = 1000


def validate_id(value: str, name: str = "id") -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ToolValidationError(f"{name} must be a non-empty string")
    return cleaned


def validate_date(value: str, name: str = "date") -> str:
    cleaned = value.strip()
    if not _DATE_RE.fullmatch(cleaned):
        raise ToolValidationError(f"{name} must be YYYY-MM-DD, got {value!r}")
    return cleaned


def validate_limit(limit: int | None) -> int | None:
    if limit is None:
        return None
    if limit < 1 or limit > _MAX_LIMIT:
        raise ToolValidationError(f"limit must be between 1 and {_MAX_LIMIT}, got {limit}")
    return limit
