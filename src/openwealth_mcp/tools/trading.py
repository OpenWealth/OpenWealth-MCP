"""MCP tool adapters for OpenWealth Trading (Order Placement) API v3.0.1.

Each adapter is a thin shim: it carries the ``Annotated`` schema that the LLM
sees and delegates the actual work to ``TradingService``.  Error handling and
logging live in ``invoke_tool``; the adapters themselves have no try/except.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from openwealth_mcp.errors import (
    OpenWealthApiError,
    OpenWealthError,
    TransportError,
)
from openwealth_mcp.logging_config import get_logger
from openwealth_mcp.trading.app import get_trading_app, set_trading_client

_log = get_logger("openwealth_mcp.tools.trading")

__all__ = ["register_trading_tools", "set_trading_client"]

_READ = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True)
_WRITE_ADDITIVE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True
)
_WRITE_IDEMPOTENT = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True
)
_WRITE_DESTRUCTIVE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True
)
_WRITE_DESTRUCTIVE_IDEMPOTENT = ToolAnnotations(
    readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=True
)

_Side = Literal["buy", "sell", "subscribe", "redeem"]
_ExecutionType = Literal["market", "limit", "stop", "stopLimit"]
_TimeInForce = Literal[
    "day",
    "goodTillCancel",
    "atTheOpening",
    "immediateOrCancel",
    "fillOrKill",
    "goodTillCrossing",
    "goodTillDate",
    "atTheClose",
    "goodThroughCrossing",
    "atCrossing",
    "goodForTime",
    "goodForAuction",
    "goodForMonth",
]


# ---------------------------------------------------------------------------
# Tool gateway — unified logging + error mapping (mirrors custody pattern)
# ---------------------------------------------------------------------------


async def invoke_tool(operation: str, awaitable: Awaitable[str]) -> str:
    """Execute a service call and map errors to safe JSON tool results."""
    _log.info("tool start operation=%s", operation)
    try:
        result = await awaitable
        _log.info("tool ok operation=%s", operation)
        return result
    except OpenWealthApiError as exc:
        _log.warning(
            "tool api error operation=%s status=%s code=%s message=%s",
            operation,
            exc.status_code,
            exc.error_code,
            exc.message,
        )
        return exc.to_tool_result()
    except TransportError as exc:
        _log.warning(
            "tool transport error operation=%s message=%s",
            operation,
            exc.message,
        )
        return exc.to_tool_result()
    except OpenWealthError as exc:
        _log.warning(
            "tool error operation=%s code=%s message=%s",
            operation,
            exc.error_code,
            exc,
        )
        return exc.to_tool_result()
    except Exception as exc:  # noqa: BLE001
        _log.exception("tool unexpected error operation=%s", operation)
        return json.dumps(
            {
                "error": True,
                "error_code": "INTERNAL_ERROR",
                "message": f"{type(exc).__name__}: unexpected failure",
                "retryable": False,
            },
            default=str,
        )


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register_trading_tools(mcp: FastMCP) -> None:
    """Register all Trading API tools on the MCP server."""

    # ------------------------------------------------------------------ #
    # Customers                                                            #
    # ------------------------------------------------------------------ #

    @mcp.tool(
        name="list_customers",
        description=(
            "OpenWealth Trading operationId=listCustomers. "
            "Returns all customers (business partners) authorised for trading. "
            "Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def list_customers(
        cursor: Annotated[
            str | None, "Opaque pagination cursor from a previous next_cursor"
        ] = None,
        limit: Annotated[int | None, "Maximum number of items to return (min 1)"] = None,
    ) -> str:
        return await invoke_tool(
            "listCustomers",
            get_trading_app().service.list_customers(cursor=cursor, limit=limit),
        )

    @mcp.tool(
        name="get_customer",
        description=(
            "OpenWealth Trading operationId=getCustomer. "
            "Returns a specific customer authorised for trading."
        ),
        annotations=_READ,
    )
    async def get_customer(
        customer_id: Annotated[str, "Bank customer id (path customerId)"],
    ) -> str:
        return await invoke_tool(
            "getCustomer",
            get_trading_app().service.get_customer(customer_id),
        )

    # ------------------------------------------------------------------ #
    # Accounts                                                             #
    # ------------------------------------------------------------------ #

    @mcp.tool(
        name="list_accounts",
        description=(
            "OpenWealth Trading operationId=listAccounts. "
            "Returns all accounts authorised for trading. "
            "Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def list_accounts(
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "listAccounts",
            get_trading_app().service.list_accounts(cursor=cursor, limit=limit),
        )

    @mcp.tool(
        name="get_account",
        description=(
            "OpenWealth Trading operationId=getAccount. "
            "Returns a specific account authorised for trading."
        ),
        annotations=_READ,
    )
    async def get_account(
        account_id: Annotated[str, "Account id"],
    ) -> str:
        return await invoke_tool(
            "getAccount",
            get_trading_app().service.get_account(account_id),
        )

    # ------------------------------------------------------------------ #
    # Orders — read                                                        #
    # ------------------------------------------------------------------ #

    @mcp.tool(
        name="list_orders",
        description=(
            "OpenWealth Trading operationId=listOrders. "
            "Returns open orders accessible to the caller. "
            "Optional filters: customer_id, account_id, status. "
            "Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def list_orders(
        customer_id: Annotated[str | None, "Filter by bank customer id"] = None,
        account_id: Annotated[str | None, "Filter by account id"] = None,
        status: Annotated[
            str | None,
            "Filter by order status (e.g. open, filled, cancelled)",
        ] = None,
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "listOrders",
            get_trading_app().service.list_orders(
                customer_id=customer_id,
                account_id=account_id,
                status=status,
                cursor=cursor,
                limit=limit,
            ),
        )

    @mcp.tool(
        name="get_order",
        description=("OpenWealth Trading operationId=getOrder. Returns a single order by id."),
        annotations=_READ,
    )
    async def get_order(
        order_id: Annotated[str, "Order id (UUID)"],
    ) -> str:
        return await invoke_tool(
            "getOrder",
            get_trading_app().service.get_order(order_id),
        )

    @mcp.tool(
        name="list_order_executions",
        description=(
            "OpenWealth Trading operationId=listOrderExecutions. "
            "Returns execution details (fills) for a given order. "
            "Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def list_order_executions(
        order_id: Annotated[str, "Order id (UUID)"],
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "listOrderExecutions",
            get_trading_app().service.list_order_executions(order_id, cursor=cursor, limit=limit),
        )

    @mcp.tool(
        name="get_order_execution",
        description=(
            "OpenWealth Trading operationId=getOrderExecution. "
            "Returns a single execution (fill) for a given order."
        ),
        annotations=_READ,
    )
    async def get_order_execution(
        order_id: Annotated[str, "Order id (UUID)"],
        execution_id: Annotated[str, "Execution id (UUID)"],
    ) -> str:
        return await invoke_tool(
            "getOrderExecution",
            get_trading_app().service.get_order_execution(order_id, execution_id),
        )

    @mcp.tool(
        name="list_order_states",
        description=(
            "OpenWealth Trading operationId=listOrderStates. "
            "Returns the list of state transitions for a given order."
        ),
        annotations=_READ,
    )
    async def list_order_states(
        order_id: Annotated[str, "Order id (UUID)"],
    ) -> str:
        return await invoke_tool(
            "listOrderStates",
            get_trading_app().service.list_order_states(order_id),
        )

    # ------------------------------------------------------------------ #
    # Orders — write                                                       #
    # ------------------------------------------------------------------ #

    @mcp.tool(
        name="create_order",
        description=(
            "OpenWealth Trading operationId=createOrder. "
            "FINANCIAL IMPACT: Posts a single-leg order to the custodian. "
            "Supports one or more allocations (bulk split across accounts). "
            "Irreversible once accepted. Confirm details with the user before calling. "
            "Not retried on failure to prevent duplicate orders."
        ),
        annotations=_WRITE_DESTRUCTIVE,
    )
    async def create_order(
        client_reference: Annotated[
            str,
            "Unique order reference assigned by the caller (e.g. 'ORD-AAPL-20260810-001').",
        ],
        isin: Annotated[str, "ISIN of the instrument to trade (e.g. 'US0378331005')."],
        side: Annotated[_Side, "Trade direction"],
        quantity: Annotated[float, "Total order quantity (units) on the order leg"],
        execution_type: Annotated[_ExecutionType, "Order type"],
        time_in_force: Annotated[_TimeInForce, "How long the order stays active"],
        allocations: Annotated[
            list[dict[str, Any]],
            (
                "One or more allocations. Each item: "
                "{debit_account_id, credit_account_id, quantity}. "
                "For a buy: debit=cash account, credit=securities account. "
                "Use one item for a single account; use multiple items to split "
                "across accounts (bulk). Allocation quantities should sum to the "
                "order quantity."
            ),
        ],
        limit_price: Annotated[
            float | None,
            "Limit price per unit (needed for limit / stopLimit)",
        ] = None,
        stop_price: Annotated[
            float | None,
            "Stop trigger price per unit (needed for stop / stopLimit)",
        ] = None,
        place_of_trade_mic: Annotated[
            str | None,
            "Market Identification Code (e.g. 'XNAS', 'XSWX')",
        ] = None,
        settlement_date: Annotated[
            str | None,
            "Requested settlement date YYYY-MM-DD",
        ] = None,
        group_reference: Annotated[
            str | None,
            "Optional group reference to link related orders",
        ] = None,
        best_effort_execution: Annotated[
            bool,
            "If true, proceed even if some allocations fail pre-trade checks",
        ] = False,
    ) -> str:
        return await invoke_tool(
            "createOrder",
            get_trading_app().service.create_order(
                client_reference,
                isin,
                side,
                quantity,
                execution_type,
                time_in_force,
                allocations,
                limit_price=limit_price,
                stop_price=stop_price,
                place_of_trade_mic=place_of_trade_mic,
                settlement_date=settlement_date,
                group_reference=group_reference,
                best_effort_execution=best_effort_execution,
            ),
        )

    @mcp.tool(
        name="cancel_order",
        description=(
            "OpenWealth Trading operationId=actionCancelOrder. "
            "FINANCIAL IMPACT: Requests cancellation of an existing open order. "
            "Confirm with the user before calling. "
            "Cancellation is idempotent (safe to retry on 5xx)."
        ),
        annotations=_WRITE_DESTRUCTIVE_IDEMPOTENT,
    )
    async def cancel_order(
        order_id: Annotated[str, "Order id (UUID) to cancel"],
        cancel_body: Annotated[
            dict[str, Any] | None,
            "Optional cancellation request body (e.g. cancellation reason)",
        ] = None,
    ) -> str:
        return await invoke_tool(
            "actionCancelOrder",
            get_trading_app().service.cancel_order(order_id, cancel_body=cancel_body),
        )

    # ------------------------------------------------------------------ #
    # Quotes                                                               #
    # ------------------------------------------------------------------ #

    @mcp.tool(
        name="create_quote",
        description=(
            "OpenWealth Trading operationId=createQuote. "
            "Requests an indicative or tradable quote for an instrument. "
            "Does not create an order — no effect on positions."
        ),
        annotations=_WRITE_IDEMPOTENT,
    )
    async def create_quote(
        quote_body: Annotated[
            dict[str, Any],
            "Quote request object conforming to the QuoteRequest schema in tradingAPI.yaml.",
        ],
    ) -> str:
        return await invoke_tool(
            "createQuote",
            get_trading_app().service.create_quote(quote_body),
        )

    # ------------------------------------------------------------------ #
    # Event subscriptions                                                  #
    # ------------------------------------------------------------------ #

    @mcp.tool(
        name="list_event_subscriptions",
        description=(
            "OpenWealth Trading operationId=listEventSubscriptions. "
            "Returns all webhook event subscriptions for the caller. "
            "Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def list_event_subscriptions(
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "listEventSubscriptions",
            get_trading_app().service.list_event_subscriptions(cursor=cursor, limit=limit),
        )

    @mcp.tool(
        name="get_event_subscription",
        description=(
            "OpenWealth Trading operationId=getEventSubscription. "
            "Returns a single event subscription by id."
        ),
        annotations=_READ,
    )
    async def get_event_subscription(
        subscription_id: Annotated[str, "Event subscription id (UUID)"],
    ) -> str:
        return await invoke_tool(
            "getEventSubscription",
            get_trading_app().service.get_event_subscription(subscription_id),
        )

    @mcp.tool(
        name="create_event_subscription",
        description=(
            "OpenWealth Trading operationId=createEventSubscription. "
            "Registers a webhook URL to receive order status notifications. "
            "Not retried to avoid creating duplicate subscriptions."
        ),
        annotations=_WRITE_ADDITIVE,
    )
    async def create_event_subscription(
        subscription_body: Annotated[
            dict[str, Any],
            "EventSubscription object with callbackUrl and eventTypes.",
        ],
    ) -> str:
        return await invoke_tool(
            "createEventSubscription",
            get_trading_app().service.create_event_subscription(subscription_body),
        )

    @mcp.tool(
        name="update_event_subscription",
        description=(
            "OpenWealth Trading operationId=updateEventSubscription. "
            "Replaces an event subscription (idempotent PUT)."
        ),
        annotations=_WRITE_IDEMPOTENT,
    )
    async def update_event_subscription(
        subscription_id: Annotated[str, "Event subscription id (UUID)"],
        subscription_body: Annotated[
            dict[str, Any],
            "Updated EventSubscription object.",
        ],
    ) -> str:
        return await invoke_tool(
            "updateEventSubscription",
            get_trading_app().service.update_event_subscription(subscription_id, subscription_body),
        )

    @mcp.tool(
        name="delete_event_subscription",
        description=(
            "OpenWealth Trading operationId=deleteEventSubscription. "
            "Deletes an event subscription by id (idempotent DELETE)."
        ),
        annotations=_WRITE_DESTRUCTIVE_IDEMPOTENT,
    )
    async def delete_event_subscription(
        subscription_id: Annotated[str, "Event subscription id (UUID)"],
    ) -> str:
        return await invoke_tool(
            "deleteEventSubscription",
            get_trading_app().service.delete_event_subscription(subscription_id),
        )

    @mcp.tool(
        name="list_event_subscription_notifications",
        description=(
            "OpenWealth Trading operationId=listEventSubscriptionEventNotifications. "
            "Returns event notifications received for a subscription. "
            "Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def list_event_subscription_notifications(
        subscription_id: Annotated[str, "Event subscription id (UUID)"],
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "listEventSubscriptionEventNotifications",
            get_trading_app().service.list_event_subscription_notifications(
                subscription_id, cursor=cursor, limit=limit
            ),
        )
