"""Domain exceptions for the OpenWealth MCP server."""

from __future__ import annotations

import json
from typing import Any


class OpenWealthError(Exception):
    """Base error for tool-facing failures."""

    error_code: str = "INTERNAL_ERROR"
    retryable: bool = False

    def to_tool_result(self) -> str:
        payload: dict[str, Any] = {
            "error": True,
            "error_code": self.error_code,
            "message": str(self),
            "retryable": self.retryable,
        }
        return json.dumps(payload, indent=2, default=str)


class ToolValidationError(OpenWealthError):
    """Invalid tool arguments before calling the upstream API."""

    error_code = "VALIDATION_ERROR"
    retryable = False

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class TransportError(OpenWealthError):
    """Network / transport failure talking to the Custody API."""

    error_code = "TRANSPORT_ERROR"
    retryable = True

    def __init__(
        self,
        message: str,
        *,
        correlation_id: str | None = None,
    ) -> None:
        self.message = message
        self.correlation_id = correlation_id
        super().__init__(message)

    def to_tool_result(self) -> str:
        payload: dict[str, Any] = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.correlation_id:
            payload["correlation_id"] = self.correlation_id
        return json.dumps(payload, indent=2, default=str)


class OpenWealthApiError(OpenWealthError):
    """Raised when the Custody API returns a non-success HTTP status."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        body: Any = None,
        correlation_id: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.body = body
        self.correlation_id = correlation_id
        self.error_code = f"UPSTREAM_{status_code}"
        self.retryable = status_code in {408, 429, 500, 502, 503, 504}
        super().__init__(f"HTTP {status_code}: {message}")

    def to_tool_result(self) -> str:
        # Do not echo raw upstream bodies to the MCP/LLM channel.
        payload: dict[str, Any] = {
            "error": True,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.correlation_id:
            payload["correlation_id"] = self.correlation_id
        return json.dumps(payload, indent=2, default=str)
