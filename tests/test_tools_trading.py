"""Trading tool registration and invocation tests."""

from __future__ import annotations

import json

import httpx
import pytest

from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.config import Settings
from openwealth_mcp.trading.app import set_trading_client
from openwealth_mcp.trading.server import mcp

_TRADING_URL = "https://api.example.com/trading-services/v1"


def _settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        trading_base_url=_TRADING_URL,
        bearer_token="test-token",
        correlation_id="tool-cid",
        max_retries=0,
        _env_file=None,
    )


def _make_client(handler: httpx.MockTransport) -> OpenWealthHttpClient:
    return OpenWealthHttpClient(settings=_settings(), base_url=_TRADING_URL, transport=handler)


def _tool_text(result: object) -> str:
    if isinstance(result, str):
        return result
    if hasattr(result, "content"):
        for part in result.content:
            if hasattr(part, "text"):
                return part.text
    if isinstance(result, list):
        for part in result:
            if hasattr(part, "text"):
                return part.text
    return str(result)


# ------------------------------------------------------------------
# Tool registration smoke test
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trading_tools_registered() -> None:
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    expected = {
        "list_customers",
        "get_customer",
        "list_accounts",
        "get_account",
        "list_orders",
        "get_order",
        "create_order",
        "cancel_order",
        "list_order_executions",
        "get_order_execution",
        "list_order_states",
        "create_quote",
        "list_event_subscriptions",
        "get_event_subscription",
        "create_event_subscription",
        "update_event_subscription",
        "delete_event_subscription",
        "list_event_subscription_notifications",
    }
    assert expected.issubset(names)


@pytest.mark.asyncio
async def test_trading_tool_annotations() -> None:
    tools = {t.name: t for t in await mcp.list_tools()}

    list_orders = tools["list_orders"]
    assert list_orders.annotations is not None
    assert list_orders.annotations.readOnlyHint is True
    assert list_orders.annotations.idempotentHint is True
    assert list_orders.annotations.openWorldHint is True

    create_order = tools["create_order"]
    assert create_order.annotations is not None
    assert create_order.annotations.readOnlyHint is False
    assert create_order.annotations.destructiveHint is True
    assert create_order.annotations.idempotentHint is False

    cancel_order = tools["cancel_order"]
    assert cancel_order.annotations is not None
    assert cancel_order.annotations.destructiveHint is True
    assert cancel_order.annotations.idempotentHint is True

    create_quote = tools["create_quote"]
    assert create_quote.annotations is not None
    assert create_quote.annotations.readOnlyHint is False
    assert create_quote.annotations.destructiveHint is False
    assert create_quote.annotations.idempotentHint is True


# ------------------------------------------------------------------
# Read tools
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_orders_tool_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"orderId": "O1", "status": "open"}])

    client = _make_client(httpx.MockTransport(handler))
    set_trading_client(client)
    try:
        result = await mcp.call_tool("list_orders", {"status": "open"})
        text = _tool_text(result)
        payload = json.loads(text)
        assert payload["data"][0]["orderId"] == "O1"
    finally:
        set_trading_client(None)
        await client.aclose()


@pytest.mark.asyncio
async def test_get_order_tool_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/orders/O42" in str(request.url)
        return httpx.Response(200, json={"orderId": "O42", "status": "filled"})

    client = _make_client(httpx.MockTransport(handler))
    set_trading_client(client)
    try:
        result = await mcp.call_tool("get_order", {"order_id": "O42"})
        payload = json.loads(_tool_text(result))
        assert payload["data"]["orderId"] == "O42"
    finally:
        set_trading_client(None)
        await client.aclose()


# ------------------------------------------------------------------
# Write tools
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_order_tool_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/orders")
        body = json.loads(request.content)
        assert body["clientReference"] == "ORD-TEST-001"
        assert body["executionType"] == "market"
        assert body["timeInForce"] == "day"
        leg = body["legList"][0]
        assert leg["side"] == "buy"
        assert leg["quantity"] == 10
        assert leg["baseInstrument"]["identification"]["identifier"] == "US0378331005"
        assert leg["quoteInstrument"]["identification"]["identifier"] == "US0378331005"
        alloc = body["allocationList"][0]["legList"][0]
        assert alloc["debitAccountId"] == "CASH-001"
        assert alloc["creditAccountId"] == "SEC-001"
        return httpx.Response(202, json={"orderId": "O99"})

    client = _make_client(httpx.MockTransport(handler))
    set_trading_client(client)
    try:
        result = await mcp.call_tool(
            "create_order",
            {
                "client_reference": "ORD-TEST-001",
                "isin": "US0378331005",
                "side": "buy",
                "quantity": 10,
                "execution_type": "market",
                "time_in_force": "day",
                "allocations": [
                    {
                        "debit_account_id": "CASH-001",
                        "credit_account_id": "SEC-001",
                        "quantity": 10,
                    }
                ],
            },
        )
        payload = json.loads(_tool_text(result))
        assert payload["data"]["orderId"] == "O99"
    finally:
        set_trading_client(None)
        await client.aclose()


@pytest.mark.asyncio
async def test_create_order_with_optional_fields() -> None:
    """Optional fields (MIC, group_reference, settlement_date) must be forwarded in the body."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["groupReference"] == "GRP-001"
        assert body["requestedPlaceOfTrade"]["marketIdentificationCode"] == "XNAS"
        assert body["legList"][0]["settlementDate"] == "2026-09-01"
        return httpx.Response(202, json={"orderId": "O77"})

    client = _make_client(httpx.MockTransport(handler))
    set_trading_client(client)
    try:
        result = await mcp.call_tool(
            "create_order",
            {
                "client_reference": "ORD-OPT-001",
                "isin": "US0378331005",
                "side": "buy",
                "quantity": 5,
                "execution_type": "market",
                "time_in_force": "day",
                "allocations": [
                    {
                        "debit_account_id": "CASH-001",
                        "credit_account_id": "SEC-001",
                        "quantity": 5,
                    }
                ],
                "place_of_trade_mic": "XNAS",
                "group_reference": "GRP-001",
                "settlement_date": "2026-09-01",
            },
        )
        payload = json.loads(_tool_text(result))
        assert payload["data"]["orderId"] == "O77"
    finally:
        set_trading_client(None)
        await client.aclose()


@pytest.mark.asyncio
async def test_create_order_tool_multiple_allocations() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert len(body["allocationList"]) == 3
        return httpx.Response(202, json={"orderId": "O-3"})

    client = _make_client(httpx.MockTransport(handler))
    set_trading_client(client)
    try:
        result = await mcp.call_tool(
            "create_order",
            {
                "client_reference": "ORD-3ALLOC",
                "isin": "US0378331005",
                "side": "buy",
                "quantity": 90,
                "execution_type": "market",
                "time_in_force": "day",
                "allocations": [
                    {
                        "debit_account_id": "C1",
                        "credit_account_id": "S1",
                        "quantity": 30,
                    },
                    {
                        "debit_account_id": "C2",
                        "credit_account_id": "S2",
                        "quantity": 30,
                    },
                    {
                        "debit_account_id": "C3",
                        "credit_account_id": "S3",
                        "quantity": 30,
                    },
                ],
            },
        )
        payload = json.loads(_tool_text(result))
        assert payload["data"]["orderId"] == "O-3"
    finally:
        set_trading_client(None)
        await client.aclose()


@pytest.mark.asyncio
async def test_cancel_order_tool_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/orders/O1/actions/cancel" in str(request.url)
        return httpx.Response(200, json={"status": "cancelled"})

    client = _make_client(httpx.MockTransport(handler))
    set_trading_client(client)
    try:
        result = await mcp.call_tool("cancel_order", {"order_id": "O1"})
        payload = json.loads(_tool_text(result))
        assert payload["data"]["status"] == "cancelled"
    finally:
        set_trading_client(None)
        await client.aclose()


@pytest.mark.asyncio
async def test_delete_subscription_tool_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        return httpx.Response(204)

    client = _make_client(httpx.MockTransport(handler))
    set_trading_client(client)
    try:
        result = await mcp.call_tool("delete_event_subscription", {"subscription_id": "S1"})
        payload = json.loads(_tool_text(result))
        assert payload["status_code"] == 204
    finally:
        set_trading_client(None)
        await client.aclose()
