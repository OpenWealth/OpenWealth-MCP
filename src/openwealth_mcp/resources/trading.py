"""MCP resource providers for OpenWealth Trading (Order Placement) API v3.0.1."""

from __future__ import annotations

from fastmcp import FastMCP

from openwealth_mcp.resources._spec_path import resolve_spec_path

_SPEC_SUMMARY = """\
# OpenWealth Trading (Order Placement) API v3.0.1

Docs: https://sandbox.openwealth.synpulse8.com/docs?api=order-placement-3-0-1

## IMPORTANT: Financial impact

`create_order` places a real financial order.  Always confirm details with the
user before calling it.  `cancel_order` is idempotent.

## Tool reference

| Tool | operationId | Method path |
|------|-------------|-------------|
| list_customers | listCustomers | GET /customers |
| get_customer | getCustomer | GET /customers/{customerId} |
| list_accounts | listAccounts | GET /accounts |
| get_account | getAccount | GET /accounts/{accountId} |
| list_orders | listOrders | GET /orders |
| get_order | getOrder | GET /orders/{orderId} |
| create_order | createOrder | POST /orders |
| cancel_order | actionCancelOrder | POST /orders/{orderId}/actions/cancel |
| list_order_executions | listOrderExecutions | GET /orders/{orderId}/executions |
| get_order_execution | getOrderExecution | GET /orders/{orderId}/executions/{executionId} |
| list_order_states | listOrderStates | GET /orders/{orderId}/states |
| create_quote | createQuote | POST /quotes |
| list_event_subscriptions | listEventSubscriptions | GET /event-subscriptions |
| get_event_subscription | getEventSubscription | GET /event-subscriptions/{id} |
| create_event_subscription | createEventSubscription | POST /event-subscriptions |
| update_event_subscription | updateEventSubscription | PUT /event-subscriptions/{id} |
| delete_event_subscription | deleteEventSubscription | DELETE /event-subscriptions/{id} |
| list_event_subscription_notifications | listEventSubscriptionEventNotifications | GET /event-subscriptions/{id}/event-notifications |
"""

_SPEC_NOT_FOUND = "tradingAPI.yaml not found; ensure specs/tradingAPI.yaml is present."


def register_trading_resources(mcp: FastMCP) -> None:
    """Register Trading spec resources on the MCP server."""

    @mcp.resource("openwealth://specs/trading")
    def trading_spec_summary() -> str:
        """Summary of Trading API v3.0.1 endpoints exposed as tools."""
        return _SPEC_SUMMARY

    @mcp.resource("openwealth://specs/trading.yaml")
    def trading_spec_yaml() -> str:
        """Vendored OpenAPI YAML for Trading (Order Placement) API v3.0.1."""
        path = resolve_spec_path("tradingAPI.yaml")
        if path is None:
            return _SPEC_NOT_FOUND
        return path.read_text(encoding="utf-8")
