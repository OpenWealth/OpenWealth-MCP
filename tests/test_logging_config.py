"""Tests for JSON logging and secret redaction."""

import json
import logging

from openwealth_mcp.logging_config import JsonFormatter, RedactingFilter, setup_logging


def test_redacting_filter_masks_bearer() -> None:
    record = logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Authorization: Bearer super-secret-token value",
        args=(),
        exc_info=None,
    )
    assert RedactingFilter().filter(record) is True
    message = record.getMessage()
    assert "super-secret-token" not in message
    assert "***" in message


def test_json_formatter_includes_extra_fields() -> None:
    record = logging.LogRecord(
        name="openwealth_mcp",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "cid-1"  # type: ignore[attr-defined]
    record.duration_ms = 12  # type: ignore[attr-defined]
    line = JsonFormatter().format(record)
    payload = json.loads(line)
    assert payload["message"] == "hello"
    assert payload["correlation_id"] == "cid-1"
    assert payload["duration_ms"] == 12


def test_setup_logging_returns_logger(tmp_path) -> None:  # type: ignore[no-untyped-def]
    log_file = tmp_path / "mcp.log"
    log = setup_logging("INFO", log_file=str(log_file))
    log.info("Authorization: Bearer abcdef.ghij")
    text = log_file.read_text(encoding="utf-8")
    assert "abcdef.ghij" not in text
    assert "***" in text
    assert '"level": "INFO"' in text
