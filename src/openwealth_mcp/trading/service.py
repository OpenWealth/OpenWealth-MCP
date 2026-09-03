"""Trading domain service — one method per OpenAPI operationId.

This layer owns all path construction and query-parameter assembly so that
the MCP tool adapters remain thin (one-liners).  It has no MCP or HTTP-
transport knowledge; it delegates every network call to ``OpenWealthHttpClient``.

API: OpenWealth Order Placement (Trading) API v3.0.1
Spec: https://github.com/swissfintechinnovations/ca-wealth/blob/main/tradingAPI.yaml
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.validation import validate_date, validate_id, validate_limit


def _seg(value: str) -> str:
    return quote(value, safe="")


class TradingService:
    """Maps OpenWealth Trading operationIds to HTTP calls."""

    def __init__(self, client: OpenWealthHttpClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Customers (trading-authorised)
    # ------------------------------------------------------------------

    async def list_customers(
        self,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """operationId: listCustomers — customers authorised for trading."""
        return await self._client.get(
            "/customers",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )

    async def get_customer(self, customer_id: str) -> str:
        """operationId: getCustomer."""
        cid = validate_id(customer_id, "customer_id")
        return await self._client.get(f"/customers/{_seg(cid)}")

    # ------------------------------------------------------------------
    # Accounts (trading-authorised)
    # ------------------------------------------------------------------

    async def list_accounts(
        self,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """operationId: listAccounts — accounts authorised for trading."""
        return await self._client.get(
            "/accounts",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )

    async def get_account(self, account_id: str) -> str:
        """operationId: getAccount."""
        aid = validate_id(account_id, "account_id")
        return await self._client.get(f"/accounts/{_seg(aid)}")

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    async def list_orders(
        self,
        *,
        customer_id: str | None = None,
        account_id: str | None = None,
        status: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """operationId: listOrders — open orders accessible to the caller."""
        cid = validate_id(customer_id, "customer_id") if customer_id is not None else None
        aid = validate_id(account_id, "account_id") if account_id is not None else None
        return await self._client.get(
            "/orders",
            params={
                "customerId": cid,
                "accountId": aid,
                "status": status,
                "cursor": cursor,
                "limit": validate_limit(limit),
            },
        )

    async def get_order(self, order_id: str) -> str:
        """operationId: getOrder."""
        oid = validate_id(order_id, "order_id")
        return await self._client.get(f"/orders/{_seg(oid)}")

    async def create_order(
        self,
        client_reference: str,
        isin: str,
        side: str,
        quantity: float,
        execution_type: str,
        time_in_force: str,
        allocations: list[dict[str, Any]],
        *,
        limit_price: float | None = None,
        stop_price: float | None = None,
        place_of_trade_mic: str | None = None,
        settlement_date: str | None = None,
        group_reference: str | None = None,
        best_effort_execution: bool = False,
    ) -> str:
        """operationId: createOrder — POST /orders (single-leg, N allocations).

        Each item in ``allocations`` must provide:
        ``debit_account_id``, ``credit_account_id``, ``quantity``.

        NOT retried: a duplicate order is a financial error.
        """
        from openwealth_mcp.errors import ToolValidationError  # avoid circular at module level

        if not allocations:
            raise ToolValidationError("allocations must contain at least one entry")
        for i, alloc in enumerate(allocations):
            if not (alloc.get("debit_account_id") or alloc.get("debitAccountId")):
                raise ToolValidationError(f"allocations[{i}] missing debit_account_id")
            if not (alloc.get("credit_account_id") or alloc.get("creditAccountId")):
                raise ToolValidationError(f"allocations[{i}] missing credit_account_id")

        leg: dict[str, Any] = {
            "index": 0,
            "side": side,
            "quantity": quantity,
            "quantityType": "unit",
            "unitReference": "baseInstrument",
            "baseInstrument": {"identification": {"identifier": isin, "type": "isin"}},
            "quoteInstrument": {"identification": {"identifier": isin, "type": "isin"}},
            "priceType": "actual",
            "positionEffect": "open",
        }
        if limit_price is not None:
            leg["limitPrice"] = limit_price
        if stop_price is not None:
            leg["stopPrice"] = stop_price
        if settlement_date is not None:
            leg["settlementDate"] = validate_date(settlement_date, "settlement_date")

        allocation_list: list[dict[str, Any]] = []
        for item in allocations:
            debit = item.get("debit_account_id") or item.get("debitAccountId")
            credit = item.get("credit_account_id") or item.get("creditAccountId")
            alloc_qty = item.get("quantity", quantity)
            allocation_list.append(
                {
                    "legList": [
                        {
                            "orderLegIndex": 0,
                            "creditAccountId": credit,
                            "debitAccountId": debit,
                            "quantity": alloc_qty,
                            "quantityType": item.get("quantity_type")
                            or item.get("quantityType")
                            or "unit",
                        }
                    ]
                }
            )

        order_body: dict[str, Any] = {
            "clientReference": client_reference,
            "executionType": execution_type,
            "timeInForce": time_in_force,
            "bestEffortExecution": best_effort_execution,
            "legList": [leg],
            "allocationList": allocation_list,
        }
        if group_reference:
            order_body["groupReference"] = group_reference
        if place_of_trade_mic:
            order_body["requestedPlaceOfTrade"] = {"marketIdentificationCode": place_of_trade_mic}

        return await self._client.post("/orders", body=order_body, idempotent=False)

    async def cancel_order(
        self,
        order_id: str,
        *,
        cancel_body: dict[str, Any] | None = None,
    ) -> str:
        """operationId: actionCancelOrder — POST /orders/{orderId}/actions/cancel.

        Cancellation is idempotent (cancelling a cancelled order is a no-op),
        so one retry is allowed on 5xx.
        """
        oid = validate_id(order_id, "order_id")
        return await self._client.post(
            f"/orders/{_seg(oid)}/actions/cancel",
            body=cancel_body,
            idempotent=True,
        )

    async def list_order_executions(
        self,
        order_id: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """operationId: listOrderExecutions."""
        oid = validate_id(order_id, "order_id")
        return await self._client.get(
            f"/orders/{_seg(oid)}/executions",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )

    async def get_order_execution(self, order_id: str, execution_id: str) -> str:
        """operationId: getOrderExecution."""
        oid = validate_id(order_id, "order_id")
        eid = validate_id(execution_id, "execution_id")
        return await self._client.get(f"/orders/{_seg(oid)}/executions/{_seg(eid)}")

    async def list_order_states(self, order_id: str) -> str:
        """operationId: listOrderStates."""
        oid = validate_id(order_id, "order_id")
        return await self._client.get(f"/orders/{_seg(oid)}/states")

    # ------------------------------------------------------------------
    # Quotes
    # ------------------------------------------------------------------

    async def create_quote(self, quote_body: dict[str, Any]) -> str:
        """operationId: createQuote — POST /quotes.

        Requesting a quote is read-like (no side-effects on positions),
        so retried on 5xx.
        """
        return await self._client.post("/quotes", body=quote_body, idempotent=True)

    # ------------------------------------------------------------------
    # Event subscriptions
    # ------------------------------------------------------------------

    async def list_event_subscriptions(
        self,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """operationId: listEventSubscriptions."""
        return await self._client.get(
            "/event-subscriptions",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )

    async def get_event_subscription(self, subscription_id: str) -> str:
        """operationId: getEventSubscription."""
        sid = validate_id(subscription_id, "subscription_id")
        return await self._client.get(f"/event-subscriptions/{_seg(sid)}")

    async def create_event_subscription(self, subscription_body: dict[str, Any]) -> str:
        """operationId: createEventSubscription — POST /event-subscriptions.

        Not retried: duplicate subscriptions could cause duplicate notifications.
        """
        return await self._client.post(
            "/event-subscriptions",
            body=subscription_body,
            idempotent=False,
        )

    async def update_event_subscription(
        self, subscription_id: str, subscription_body: dict[str, Any]
    ) -> str:
        """operationId: updateEventSubscription — PUT /event-subscriptions/{id}."""
        sid = validate_id(subscription_id, "subscription_id")
        return await self._client.put(
            f"/event-subscriptions/{_seg(sid)}",
            body=subscription_body,
        )

    async def delete_event_subscription(self, subscription_id: str) -> str:
        """operationId: deleteEventSubscription — DELETE /event-subscriptions/{id}."""
        sid = validate_id(subscription_id, "subscription_id")
        return await self._client.delete(f"/event-subscriptions/{_seg(sid)}")

    async def list_event_subscription_notifications(
        self,
        subscription_id: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """operationId: listEventSubscriptionEventNotifications."""
        sid = validate_id(subscription_id, "subscription_id")
        return await self._client.get(
            f"/event-subscriptions/{_seg(sid)}/event-notifications",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )
