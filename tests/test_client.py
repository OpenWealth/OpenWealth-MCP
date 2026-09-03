"""HTTP client tests with MockTransport."""

import json

import httpx
import pytest

from openwealth_mcp.client import OpenWealthApiError, OpenWealthHttpClient
from openwealth_mcp.config import Settings

_CUSTODY_URL = "https://api.example.com/api/custody-services/v3"


def _settings(max_retries: int = 0) -> Settings:
    return Settings(  # type: ignore[call-arg]
        custody_base_url=_CUSTODY_URL,
        bearer_token="test-token",
        correlation_id="fixed-cid",
        max_retries=max_retries,
        _env_file=None,
    )


def _client(settings: Settings, transport: httpx.MockTransport) -> OpenWealthHttpClient:
    return OpenWealthHttpClient(
        settings=settings,
        base_url=_CUSTODY_URL,
        transport=transport,
    )


@pytest.mark.asyncio
async def test_get_customers_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers")
        assert request.headers.get("Authorization") == "Bearer test-token"
        assert request.headers.get("X-Correlation-ID") == "fixed-cid"
        assert request.url.params.get("limit") == "2"
        return httpx.Response(
            200,
            json=[{"id": "C1", "number": "1"}],
            headers={"X-Correlation-ID": "fixed-cid", "nextCursor": "abc"},
        )

    transport = httpx.MockTransport(handler)
    async with _client(_settings(), transport) as client:
        raw = await client.get("/customers", params={"limit": 2})
    payload = json.loads(raw)
    assert payload["status_code"] == 200
    assert payload["data"][0]["id"] == "C1"
    assert payload["next_cursor"] == "abc"
    assert payload["correlation_id"] == "fixed-cid"


@pytest.mark.asyncio
async def test_get_positions_with_date_and_eod() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/customers/C1/positions" in str(request.url)
        assert request.url.params["date"] == "2024-12-31"
        assert request.url.params["end_of_day_indicator"] == "true"
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)
    async with _client(_settings(), transport) as client:
        raw = await client.get(
            "/customers/C1/positions",
            params={"date": "2024-12-31", "end_of_day_indicator": True},
        )
    assert json.loads(raw)["data"] == []


@pytest.mark.asyncio
async def test_api_error_401() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"title": "Unauthorized", "detail": "Invalid token"},
            headers={"X-Correlation-ID": "fixed-cid"},
        )

    transport = httpx.MockTransport(handler)
    async with _client(_settings(), transport) as client:
        with pytest.raises(OpenWealthApiError) as exc_info:
            await client.get("/customers")
    err = exc_info.value
    assert err.status_code == 401
    assert "Invalid token" in err.message
    tool = json.loads(err.to_tool_result())
    assert tool["error"] is True
    assert "body" not in tool


@pytest.mark.asyncio
async def test_transport_error_after_retries() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    settings = _settings(max_retries=1)
    transport = httpx.MockTransport(handler)
    from openwealth_mcp.errors import TransportError

    async with _client(settings, transport) as client:
        with pytest.raises(TransportError):
            await client.get("/customers")


@pytest.mark.asyncio
async def test_retries_on_503_then_success() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, json={"detail": "busy"})
        return httpx.Response(200, json=[{"id": "C1"}])

    settings = _settings(max_retries=1)
    transport = httpx.MockTransport(handler)
    async with _client(settings, transport) as client:
        raw = await client.get("/customers")
    assert calls["n"] == 2
    assert json.loads(raw)["data"][0]["id"] == "C1"
