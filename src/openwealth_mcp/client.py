"""HTTP client for OpenWealth Custody and Trading Services APIs."""

from __future__ import annotations

import asyncio
import email.utils
import json
import logging
import random
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from openwealth_mcp.config import Settings, get_settings
from openwealth_mcp.errors import OpenWealthApiError, TransportError
from openwealth_mcp.logging_config import get_logger

logger = get_logger("openwealth_mcp.client")

# Re-export so existing imports from this module continue to work.
__all__ = ["OpenWealthApiError", "OpenWealthHttpClient"]

_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


class OpenWealthHttpClient:
    """Thin async wrapper around httpx for OpenWealth API endpoints."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        base_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        # base_url must be supplied explicitly; Settings no longer has a single
        # shared base_url field — each service has its own.
        if base_url is None:
            raise TypeError(
                "base_url is required. "
                "Pass settings.base_url_for('custody') or settings.base_url_for('trading')."
            )
        self.base_url = base_url
        auth = self.settings.authorization_header()
        headers: dict[str, str] = {
            "Accept": "application/json",
        }
        if auth:
            headers["Authorization"] = auth

        timeout = httpx.Timeout(
            connect=self.settings.connect_timeout_seconds,
            read=self.settings.timeout_seconds,
            write=self.settings.timeout_seconds,
            pool=self.settings.connect_timeout_seconds,
        )
        limits = httpx.Limits(
            max_connections=20,
            max_keepalive_connections=10,
        )

        logger.info(
            "HTTP client ready base_url=%s auth_configured=%s timeout=%ss retries=%s",
            self.base_url,
            "yes" if auth else "no",
            self.settings.timeout_seconds,
            self.settings.max_retries,
        )

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            verify=self.settings.verify_tls,
            limits=limits,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> OpenWealthHttpClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def _correlation_id(self, override: str | None = None) -> str:
        return override or self.settings.correlation_id or str(uuid.uuid4())

    def _request_headers(self, correlation_id: str) -> dict[str, str]:
        # Custody API uses X-Correlation-ID; Trading API uses Correlation-Id (required).
        # Sending both ensures compatibility without per-server configuration.
        return {
            "X-Correlation-ID": correlation_id,
            "Correlation-Id": correlation_id,
        }

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> str:
        """Perform GET and return a JSON string suitable for MCP tool output."""
        cid = self._correlation_id(correlation_id)
        query = _clean_params(params)
        url = f"{self.base_url}{path}"
        attempts = self.settings.max_retries + 1
        last_error: Exception | None = None
        request_headers = self._request_headers(cid)

        for attempt in range(1, attempts + 1):
            started = time.perf_counter()
            logger.info(
                "GET %s params=%s correlation_id=%s attempt=%s/%s",
                url,
                query,
                cid,
                attempt,
                attempts,
            )
            try:
                response = await self._client.get(
                    path,
                    params=query,
                    headers=request_headers,
                )
            except httpx.RequestError as exc:
                duration_ms = int((time.perf_counter() - started) * 1000)
                logger.warning(
                    "HTTP transport error GET %s attempt=%s duration_ms=%s err=%s",
                    url,
                    attempt,
                    duration_ms,
                    type(exc).__name__,
                )
                last_error = exc
                if attempt < attempts:
                    await asyncio.sleep(_backoff_seconds(attempt))
                    continue
                raise TransportError(
                    f"{type(exc).__name__}: {exc}",
                    correlation_id=cid,
                ) from exc

            duration_ms = int((time.perf_counter() - started) * 1000)
            response_cid = (
                response.headers.get("X-Correlation-ID")
                or response.headers.get("Correlation-Id")
                or cid
            )
            next_cursor = response.headers.get("nextCursor") or response.headers.get(
                "X-Next-Cursor"
            )

            body: Any
            if response.content:
                try:
                    body = response.json()
                except ValueError:
                    body = response.text
            else:
                body = None

            if response.status_code >= 400:
                message = _error_message(body) or response.reason_phrase or "Request failed"
                logger.warning(
                    "GET %s -> %s correlation_id=%s duration_ms=%s message=%s",
                    url,
                    response.status_code,
                    response_cid,
                    duration_ms,
                    message,
                )
                if response.status_code in _RETRYABLE_STATUS and attempt < attempts:
                    await asyncio.sleep(_backoff_seconds(attempt, response=response))
                    continue
                raise OpenWealthApiError(
                    response.status_code,
                    message,
                    body=body,
                    correlation_id=response_cid,
                )

            logger.info(
                "GET %s -> %s correlation_id=%s duration_ms=%s next_cursor=%s",
                url,
                response.status_code,
                response_cid,
                duration_ms,
                next_cursor,
            )
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "GET %s response truncated=%s",
                    url,
                    _truncate(body, limit=500),
                )

            result: dict[str, Any] = {
                "status_code": response.status_code,
                "correlation_id": response_cid,
                "data": body,
            }
            if next_cursor is not None:
                result["next_cursor"] = next_cursor
            return json.dumps(result, indent=2, default=str)

        raise TransportError(
            f"Request failed after retries: {last_error}",
            correlation_id=cid,
        )

    # ------------------------------------------------------------------
    # Write helpers (POST / PUT / DELETE)
    # ------------------------------------------------------------------

    async def post(
        self,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        idempotent: bool = False,
    ) -> str:
        """Perform POST.

        Non-idempotent by default (``idempotent=False`` → no automatic retry).
        Pass ``idempotent=True`` for cancel/quote calls that are safe to retry.
        """
        max_attempts = (self.settings.max_retries + 1) if idempotent else 1
        return await self._write(
            "POST",
            path,
            body=body,
            params=params,
            correlation_id=correlation_id,
            max_attempts=max_attempts,
        )

    async def put(
        self,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> str:
        """Perform PUT (idempotent — full retry on 5xx)."""
        return await self._write(
            "PUT",
            path,
            body=body,
            params=params,
            correlation_id=correlation_id,
            max_attempts=self.settings.max_retries + 1,
        )

    async def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> str:
        """Perform DELETE (idempotent — full retry on 5xx)."""
        return await self._write(
            "DELETE",
            path,
            params=params,
            correlation_id=correlation_id,
            max_attempts=self.settings.max_retries + 1,
        )

    async def _write(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        max_attempts: int,
    ) -> str:
        """Low-level request executor for mutating HTTP methods."""
        cid = self._correlation_id(correlation_id)
        query = _clean_params(params)
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None
        extra_headers: dict[str, str] = {}
        if body is not None:
            extra_headers["Content-Type"] = "application/json"

        for attempt in range(1, max_attempts + 1):
            started = time.perf_counter()
            request_headers = {**self._request_headers(cid), **extra_headers}
            logger.info(
                "%s %s params=%s correlation_id=%s attempt=%s/%s",
                method,
                url,
                query,
                cid,
                attempt,
                max_attempts,
            )
            try:
                response = await self._client.request(
                    method,
                    path,
                    json=body,
                    params=query,
                    headers=request_headers,
                )
            except httpx.RequestError as exc:
                duration_ms = int((time.perf_counter() - started) * 1000)
                logger.warning(
                    "HTTP transport error %s %s attempt=%s duration_ms=%s err=%s",
                    method,
                    url,
                    attempt,
                    duration_ms,
                    type(exc).__name__,
                )
                last_error = exc
                if attempt < max_attempts:
                    await asyncio.sleep(_backoff_seconds(attempt))
                    continue
                raise TransportError(
                    f"{type(exc).__name__}: {exc}",
                    correlation_id=cid,
                ) from exc

            duration_ms = int((time.perf_counter() - started) * 1000)
            response_cid = (
                response.headers.get("X-Correlation-ID")
                or response.headers.get("Correlation-Id")
                or cid
            )

            resp_body: Any
            if response.content:
                try:
                    resp_body = response.json()
                except ValueError:
                    resp_body = response.text
            else:
                resp_body = None

            if response.status_code >= 400:
                message = _error_message(resp_body) or response.reason_phrase or "Request failed"
                logger.warning(
                    "%s %s -> %s correlation_id=%s duration_ms=%s message=%s",
                    method,
                    url,
                    response.status_code,
                    response_cid,
                    duration_ms,
                    message,
                )
                if response.status_code in _RETRYABLE_STATUS and attempt < max_attempts:
                    await asyncio.sleep(_backoff_seconds(attempt, response=response))
                    continue
                raise OpenWealthApiError(
                    response.status_code,
                    message,
                    body=resp_body,
                    correlation_id=response_cid,
                )

            logger.info(
                "%s %s -> %s correlation_id=%s duration_ms=%s",
                method,
                url,
                response.status_code,
                response_cid,
                duration_ms,
            )

            result: dict[str, Any] = {
                "status_code": response.status_code,
                "correlation_id": response_cid,
                "data": resp_body,
            }
            return json.dumps(result, indent=2, default=str)

        raise TransportError(
            f"Request failed after retries: {last_error}",
            correlation_id=cid,
        )


def _backoff_seconds(attempt: int, response: httpx.Response | None = None) -> float:
    """Compute retry delay with ±20 % jitter.

    If the response carries a ``Retry-After`` header (seconds or HTTP-date),
    that value is used as the base delay instead of the exponential backoff.
    The result is always jittered to avoid thundering-herd when multiple
    clients are retrying at the same time.
    """
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                base = float(retry_after)
                return _jitter(base)
            except ValueError:
                try:
                    parsed = email.utils.parsedate_to_datetime(retry_after)
                    remaining = (parsed - datetime.now(tz=UTC)).total_seconds()
                    if remaining > 0:
                        return _jitter(min(remaining, 300.0))
                except Exception:
                    pass
    base = min(0.25 * (2 ** (attempt - 1)), 2.0)
    return _jitter(base)


def _jitter(seconds: float) -> float:
    """Apply ±20 % multiplicative jitter to a delay value."""
    return seconds * random.uniform(0.8, 1.2)


def _truncate(value: Any, limit: int = 500) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _clean_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    if not params:
        return None
    cleaned: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            cleaned[key] = "true" if value else "false"
        else:
            cleaned[key] = value
    return cleaned or None


def _error_message(body: Any) -> str | None:
    if isinstance(body, dict):
        for key in ("detail", "title", "message", "type"):
            value = body.get(key)
            if isinstance(value, str) and value:
                return value
        errors = body.get("errors")
        if isinstance(errors, list) and errors:
            return json.dumps(errors, default=str)
    if isinstance(body, str) and body:
        return body
    return None
