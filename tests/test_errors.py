"""Tests for OpenWealthApiError and related tool envelopes."""

import json

from openwealth_mcp.errors import (
    OpenWealthApiError,
    ToolValidationError,
    TransportError,
)


def test_to_tool_result_minimal() -> None:
    err = OpenWealthApiError(404, "Not found")
    payload = json.loads(err.to_tool_result())
    assert payload["error"] is True
    assert payload["status_code"] == 404
    assert payload["message"] == "Not found"
    assert payload["error_code"] == "UPSTREAM_404"
    assert payload["retryable"] is False
    assert "correlation_id" not in payload
    assert "body" not in payload


def test_to_tool_result_sanitized() -> None:
    err = OpenWealthApiError(
        401,
        "Unauthorized",
        body={"detail": "bad token", "secret": "should-not-leak"},
        correlation_id="abc-123",
    )
    payload = json.loads(err.to_tool_result())
    assert payload["correlation_id"] == "abc-123"
    assert "body" not in payload
    assert payload["error_code"] == "UPSTREAM_401"


def test_retryable_5xx() -> None:
    err = OpenWealthApiError(503, "Unavailable")
    assert err.retryable is True


def test_str_representation() -> None:
    err = OpenWealthApiError(500, "Server error")
    assert "500" in str(err)
    assert "Server error" in str(err)


def test_transport_and_validation_envelopes() -> None:
    transport = json.loads(TransportError("timeout", correlation_id="c1").to_tool_result())
    assert transport["error_code"] == "TRANSPORT_ERROR"
    assert transport["retryable"] is True
    assert transport["correlation_id"] == "c1"

    validation = json.loads(ToolValidationError("bad date").to_tool_result())
    assert validation["error_code"] == "VALIDATION_ERROR"
    assert validation["retryable"] is False


def test_importable_from_client_module() -> None:
    """Backwards-compatibility: client.py re-exports OpenWealthApiError."""
    from openwealth_mcp.client import OpenWealthApiError as ClientAlias

    assert ClientAlias is OpenWealthApiError
