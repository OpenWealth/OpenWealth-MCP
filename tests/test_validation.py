"""Tests for argument validation helpers."""

import pytest

from openwealth_mcp.errors import ToolValidationError
from openwealth_mcp.validation import validate_date, validate_id, validate_limit


def test_validate_id_ok() -> None:
    assert validate_id(" C1 ", "customer_id") == "C1"


def test_validate_id_empty() -> None:
    with pytest.raises(ToolValidationError, match="customer_id"):
        validate_id("  ", "customer_id")


def test_validate_date_ok() -> None:
    assert validate_date("2024-05-07") == "2024-05-07"


def test_validate_date_bad() -> None:
    with pytest.raises(ToolValidationError, match="YYYY-MM-DD"):
        validate_date("05/07/2024")


def test_validate_limit_bounds() -> None:
    assert validate_limit(None) is None
    assert validate_limit(10) == 10
    with pytest.raises(ToolValidationError):
        validate_limit(0)
    with pytest.raises(ToolValidationError):
        validate_limit(1001)
