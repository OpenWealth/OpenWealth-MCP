"""Unit tests for CustodyService — validates path building and param assembly."""

import json

import httpx
import pytest

from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.config import Settings
from openwealth_mcp.custody.service import CustodyService

_CUSTODY_URL = "https://api.example.com/api/custody-services/v3"


def _settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        custody_base_url=_CUSTODY_URL,
        bearer_token="svc-token",
        correlation_id="svc-cid",
        max_retries=0,
        _env_file=None,
    )


def _make_service(handler) -> tuple[CustodyService, OpenWealthHttpClient]:
    client = OpenWealthHttpClient(
        settings=_settings(),
        base_url=_CUSTODY_URL,
        transport=httpx.MockTransport(handler),
    )
    return CustodyService(client), client


@pytest.mark.asyncio
async def test_get_customers_path_and_params() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers")
        assert request.url.params.get("limit") == "5"
        assert "cursor" not in request.url.params
        return httpx.Response(200, json=[{"id": "C1"}])

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_customers(limit=5)
    assert json.loads(raw)["data"][0]["id"] == "C1"


@pytest.mark.asyncio
async def test_get_customer_by_id_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C42")
        return httpx.Response(200, json={"id": "C42"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_customer_by_id("C42")
    assert json.loads(raw)["data"]["id"] == "C42"


@pytest.mark.asyncio
async def test_path_encodes_special_characters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        # httpx decodes .path; raw URL must keep percent-encoding.
        assert "customers/a%2Fb" in str(request.url)
        return httpx.Response(200, json={"id": "a/b"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_customer_by_id("a/b")
    assert json.loads(raw)["data"]["id"] == "a/b"


@pytest.mark.asyncio
async def test_invalid_date_raises_before_http() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=[])

    service, client = _make_service(handler)
    async with client:
        with pytest.raises(Exception, match="YYYY-MM-DD"):
            await service.get_customer_positions("C1", "not-a-date")
    assert calls["n"] == 0


@pytest.mark.asyncio
async def test_get_customer_accounts_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/accounts")
        return httpx.Response(200, json=[])

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_customer_accounts("C1")
    assert json.loads(raw)["data"] == []


@pytest.mark.asyncio
async def test_get_customer_account_by_id_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/accounts/A99")
        return httpx.Response(200, json={"id": "A99"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_customer_account_by_id("C1", "A99")
    assert json.loads(raw)["data"]["id"] == "A99"


@pytest.mark.asyncio
async def test_get_customer_positions_with_eod() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/positions")
        assert request.url.params["date"] == "2024-12-31"
        assert request.url.params["end_of_day_indicator"] == "true"
        return httpx.Response(200, json=[])

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_customer_positions("C1", "2024-12-31", end_of_day_indicator=True)
    assert json.loads(raw)["data"] == []


@pytest.mark.asyncio
async def test_get_account_positions_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/accounts/A1/positions")
        assert request.url.params["date"] == "2024-05-07"
        return httpx.Response(200, json=[{"id": "P1"}])

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_account_positions("A1", "2024-05-07")
    assert json.loads(raw)["data"][0]["id"] == "P1"


@pytest.mark.asyncio
async def test_get_customer_transactions_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/transactions")
        assert request.url.params["date"] == "2024-05-07"
        return httpx.Response(200, json=[{"id": "T1"}])

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_customer_transactions("C1", "2024-05-07")
    assert json.loads(raw)["data"][0]["id"] == "T1"


@pytest.mark.asyncio
async def test_get_transaction_by_id_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/transactions/T99")
        return httpx.Response(200, json={"id": "T99"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_transaction_by_id("C1", "T99")
    assert json.loads(raw)["data"]["id"] == "T99"
