"""TradingService tests with MockTransport."""

from __future__ import annotations

import json

import httpx
import pytest

from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.config import Settings
from openwealth_mcp.trading.service import TradingService

_TRADING_URL = "https://api.example.com/trading-services/v1"


def _settings(max_retries: int = 0) -> Settings:
    return Settings(  # type: ignore[call-arg]
        trading_base_url=_TRADING_URL,
        bearer_token="test-token",
        correlation_id="fixed-cid",
        max_retries=max_retries,
        _env_file=None,
    )


def _make_service(
    handler: httpx.MockTransport | None = None,
) -> tuple[TradingService, OpenWealthHttpClient]:
    transport = handler or httpx.MockTransport(lambda r: httpx.Response(200, json=[]))
    client = OpenWealthHttpClient(settings=_settings(), base_url=_TRADING_URL, transport=transport)
    return TradingService(client), client


# ------------------------------------------------------------------
# Customers
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_customers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers")
        assert request.method == "GET"
        return httpx.Response(200, json=[{"id": "C1"}])

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.list_customers(limit=5)
    payload = json.loads(raw)
    assert payload["data"][0]["id"] == "C1"


@pytest.mark.asyncio
async def test_get_customer() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/customers/C1" in str(request.url)
        return httpx.Response(200, json={"id": "C1"})

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.get_customer("C1")
    assert json.loads(raw)["data"]["id"] == "C1"


# ------------------------------------------------------------------
# Accounts
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_accounts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/accounts")
        return httpx.Response(200, json=[{"id": "A1"}])

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.list_accounts()
    assert json.loads(raw)["data"][0]["id"] == "A1"


# ------------------------------------------------------------------
# Orders — read
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_orders_with_filters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/orders")
        assert request.url.params.get("customerId") == "C1"
        assert request.url.params.get("status") == "open"
        return httpx.Response(200, json=[{"orderId": "O1"}])

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.list_orders(customer_id="C1", status="open")
    assert json.loads(raw)["data"][0]["orderId"] == "O1"


@pytest.mark.asyncio
async def test_get_order() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/orders/O1" in str(request.url)
        return httpx.Response(200, json={"orderId": "O1", "status": "open"})

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.get_order("O1")
    assert json.loads(raw)["data"]["orderId"] == "O1"


@pytest.mark.asyncio
async def test_list_order_executions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/orders/O1/executions" in str(request.url)
        return httpx.Response(200, json=[{"executionId": "E1"}])

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.list_order_executions("O1")
    assert json.loads(raw)["data"][0]["executionId"] == "E1"


@pytest.mark.asyncio
async def test_list_order_states() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/orders/O1/states" in str(request.url)
        return httpx.Response(200, json=[{"state": "acknowledged"}])

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.list_order_states("O1")
    assert json.loads(raw)["data"][0]["state"] == "acknowledged"


# ------------------------------------------------------------------
# Orders — write
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_order_sends_post_no_retry() -> None:
    calls: dict[str, int] = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        assert request.method == "POST"
        assert request.url.path.endswith("/orders")
        body = json.loads(request.content)
        assert body["clientReference"] == "ORD-1"
        assert body["executionType"] == "market"
        assert body["legList"][0]["side"] == "buy"
        assert len(body["allocationList"]) == 1
        alloc = body["allocationList"][0]["legList"][0]
        assert alloc["debitAccountId"] == "CASH-001"
        assert alloc["creditAccountId"] == "SEC-001"
        return httpx.Response(202, json={"orderId": "O99"})

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.create_order(
            "ORD-1",
            "US0378331005",
            "buy",
            10,
            "market",
            "day",
            [
                {
                    "debit_account_id": "CASH-001",
                    "credit_account_id": "SEC-001",
                    "quantity": 10,
                }
            ],
        )

    assert calls["n"] == 1
    assert json.loads(raw)["data"]["orderId"] == "O99"


@pytest.mark.asyncio
async def test_create_order_multiple_allocations() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["legList"][0]["quantity"] == 120
        assert len(body["allocationList"]) == 3
        qtys = [a["legList"][0]["quantity"] for a in body["allocationList"]]
        assert qtys == [40, 40, 40]
        assert body["allocationList"][1]["legList"][0]["debitAccountId"] == "CASH-2"
        return httpx.Response(202, json={"orderId": "O-MULTI"})

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.create_order(
            "ORD-MULTI",
            "US0378331005",
            "buy",
            120,
            "market",
            "day",
            [
                {
                    "debit_account_id": "CASH-1",
                    "credit_account_id": "SEC-1",
                    "quantity": 40,
                },
                {
                    "debit_account_id": "CASH-2",
                    "credit_account_id": "SEC-2",
                    "quantity": 40,
                },
                {
                    "debit_account_id": "CASH-3",
                    "credit_account_id": "SEC-3",
                    "quantity": 40,
                },
            ],
        )
    assert json.loads(raw)["data"]["orderId"] == "O-MULTI"


@pytest.mark.asyncio
async def test_create_order_not_retried_on_503() -> None:
    """create_order must NOT retry even on 5xx — prevents duplicate orders."""
    calls: dict[str, int] = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(503, json={"detail": "busy"})

    settings = Settings(  # type: ignore[call-arg]
        trading_base_url=_TRADING_URL,
        bearer_token="test-token",
        max_retries=2,
        _env_file=None,
    )
    transport = httpx.MockTransport(handler)
    client = OpenWealthHttpClient(settings=settings, base_url=_TRADING_URL, transport=transport)
    svc = TradingService(client)

    from openwealth_mcp.client import OpenWealthApiError

    async with client:
        with pytest.raises(OpenWealthApiError) as exc_info:
            await svc.create_order(
                "ORD-1",
                "US0378331005",
                "buy",
                10,
                "market",
                "day",
                [
                    {
                        "debit_account_id": "CASH-001",
                        "credit_account_id": "SEC-001",
                        "quantity": 10,
                    }
                ],
            )

    assert calls["n"] == 1, "create_order must not retry"
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_cancel_order_is_idempotent() -> None:
    """cancel_order retries on 5xx because cancellation is idempotent."""
    calls: dict[str, int] = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        assert "/orders/O1/actions/cancel" in str(request.url)
        if calls["n"] == 1:
            return httpx.Response(503, json={"detail": "busy"})
        return httpx.Response(200, json={"status": "cancelled"})

    settings = Settings(  # type: ignore[call-arg]
        trading_base_url=_TRADING_URL,
        bearer_token="test-token",
        max_retries=1,
        _env_file=None,
    )
    transport = httpx.MockTransport(handler)
    client = OpenWealthHttpClient(settings=settings, base_url=_TRADING_URL, transport=transport)
    svc = TradingService(client)

    async with client:
        raw = await svc.cancel_order("O1")

    assert calls["n"] == 2, "cancel_order should have retried once"
    assert json.loads(raw)["data"]["status"] == "cancelled"


# ------------------------------------------------------------------
# Quotes
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_quote() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/quotes")
        return httpx.Response(200, json={"quoteId": "Q1", "price": "100.50"})

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.create_quote({"instrument": "ISIN123", "side": "buy"})
    assert json.loads(raw)["data"]["quoteId"] == "Q1"


# ------------------------------------------------------------------
# Event subscriptions
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_event_subscriptions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/event-subscriptions")
        assert request.method == "GET"
        return httpx.Response(200, json=[{"id": "S1"}])

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.list_event_subscriptions()
    assert json.loads(raw)["data"][0]["id"] == "S1"


@pytest.mark.asyncio
async def test_delete_event_subscription() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert "/event-subscriptions/S1" in str(request.url)
        return httpx.Response(204)

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.delete_event_subscription("S1")
    payload = json.loads(raw)
    assert payload["status_code"] == 204
    assert payload["data"] is None


@pytest.mark.asyncio
async def test_update_event_subscription() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert "/event-subscriptions/S1" in str(request.url)
        body = json.loads(request.content)
        assert body["callbackUrl"] == "https://example.com/hook"
        return httpx.Response(200, json={"id": "S1", "callbackUrl": "https://example.com/hook"})

    svc, client = _make_service(httpx.MockTransport(handler))
    async with client:
        raw = await svc.update_event_subscription("S1", {"callbackUrl": "https://example.com/hook"})
    assert json.loads(raw)["data"]["id"] == "S1"


# ------------------------------------------------------------------
# Validation — symmetric with custody
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_orders_validates_customer_id() -> None:
    from openwealth_mcp.errors import ToolValidationError

    svc, client = _make_service()
    async with client:
        with pytest.raises(ToolValidationError):
            await svc.list_orders(customer_id="")


@pytest.mark.asyncio
async def test_list_orders_validates_account_id() -> None:
    from openwealth_mcp.errors import ToolValidationError

    svc, client = _make_service()
    async with client:
        with pytest.raises(ToolValidationError):
            await svc.list_orders(account_id="")


@pytest.mark.asyncio
async def test_create_order_rejects_empty_allocations() -> None:
    from openwealth_mcp.errors import ToolValidationError

    svc, client = _make_service()
    async with client:
        with pytest.raises(ToolValidationError, match="allocations"):
            await svc.create_order(
                client_reference="REF1",
                isin="US0378331005",
                side="buy",
                quantity=1.0,
                execution_type="market",
                time_in_force="day",
                allocations=[],
            )


@pytest.mark.asyncio
async def test_create_order_rejects_missing_debit_account() -> None:
    from openwealth_mcp.errors import ToolValidationError

    svc, client = _make_service()
    async with client:
        with pytest.raises(ToolValidationError, match="debit_account_id"):
            await svc.create_order(
                client_reference="REF1",
                isin="US0378331005",
                side="buy",
                quantity=1.0,
                execution_type="market",
                time_in_force="day",
                allocations=[{"credit_account_id": "C1", "quantity": 1.0}],
            )


@pytest.mark.asyncio
async def test_create_order_validates_settlement_date() -> None:
    from openwealth_mcp.errors import ToolValidationError

    svc, client = _make_service()
    async with client:
        with pytest.raises(ToolValidationError, match="settlement_date"):
            await svc.create_order(
                client_reference="REF1",
                isin="US0378331005",
                side="buy",
                quantity=1.0,
                execution_type="market",
                time_in_force="day",
                allocations=[{"debit_account_id": "D1", "credit_account_id": "C1"}],
                settlement_date="not-a-date",
            )
