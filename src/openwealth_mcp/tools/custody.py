"""MCP tool adapters for Custody Services v3.2.0.

Each adapter is a thin shim: it carries the ``Annotated`` schema that the LLM
sees and delegates the actual work to ``CustodyService``.  Error handling and
logging live in ``invoke_tool``; the adapters themselves have no try/except.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable
from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from openwealth_mcp.app import get_app, set_client  # re-export set_client for tests
from openwealth_mcp.errors import (
    OpenWealthApiError,
    OpenWealthError,
    TransportError,
)
from openwealth_mcp.logging_config import get_logger

_log = get_logger("openwealth_mcp.tools")

__all__ = ["register_custody_tools", "set_client"]

_READ = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True)


# ---------------------------------------------------------------------------
# Tool gateway — unified logging + error mapping
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


def register_custody_tools(mcp: FastMCP) -> None:
    """Register all Custody Services GET tools on the MCP server."""

    @mcp.tool(
        name="get_customers",
        description=(
            "OpenWealth Custody operationId=getCustomers. "
            "Returns all customers (business partners) accessible for the logged-in user. "
            "Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def get_customers(
        cursor: Annotated[
            str | None, "Opaque pagination cursor from a previous next_cursor"
        ] = None,
        limit: Annotated[int | None, "Maximum number of items to return (min 1)"] = None,
    ) -> str:
        return await invoke_tool(
            "getCustomers",
            get_app().service.get_customers(cursor=cursor, limit=limit),
        )

    @mcp.tool(
        name="get_customers_by_customer_id",
        description=(
            "OpenWealth Custody operationId=getCustomersByCustomerId. "
            "Returns a specific customer by id."
        ),
        annotations=_READ,
    )
    async def get_customers_by_customer_id(
        customer_id: Annotated[str, "Bank customer id (path customerId)"],
    ) -> str:
        return await invoke_tool(
            "getCustomersByCustomerId",
            get_app().service.get_customer_by_id(customer_id),
        )

    @mcp.tool(
        name="get_customer_accounts_by_customer_id",
        description=(
            "OpenWealth Custody operationId=getCustomerAccountsByCustomerId. "
            "Returns accounts for a customer. Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def get_customer_accounts_by_customer_id(
        customer_id: Annotated[str, "Bank customer id (path customerId)"],
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "getCustomerAccountsByCustomerId",
            get_app().service.get_customer_accounts(customer_id, cursor=cursor, limit=limit),
        )

    @mcp.tool(
        name="get_customer_account_by_id",
        description=(
            "OpenWealth Custody operationId=getCustomerAccountById. "
            "Returns a specific customer account by accountId."
        ),
        annotations=_READ,
    )
    async def get_customer_account_by_id(
        customer_id: Annotated[str, "Bank customer id (path customerId)"],
        account_id: Annotated[str, "Account id (not IBAN)"],
    ) -> str:
        return await invoke_tool(
            "getCustomerAccountById",
            get_app().service.get_customer_account_by_id(customer_id, account_id),
        )

    @mcp.tool(
        name="get_customer_position_by_customer_id",
        description=(
            "OpenWealth Custody operationId=getCustomerPositionByCustomerId. "
            "Returns positions for a customer on the given date (YYYY-MM-DD). "
            "Optional end_of_day_indicator filters EOD-confirmed resources."
        ),
        annotations=_READ,
    )
    async def get_customer_position_by_customer_id(
        customer_id: Annotated[str, "Bank customer id (path customerId)"],
        date: Annotated[str, "Valuation date YYYY-MM-DD (required by OpenAPI)"],
        end_of_day_indicator: Annotated[
            bool | None,
            "If true only EOD-confirmed; if false only non-EOD; omit for all",
        ] = None,
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "getCustomerPositionByCustomerId",
            get_app().service.get_customer_positions(
                customer_id,
                date,
                end_of_day_indicator=end_of_day_indicator,
                cursor=cursor,
                limit=limit,
            ),
        )

    @mcp.tool(
        name="get_customer_position_by_id",
        description=(
            "OpenWealth Custody operationId=getCustomerPositionById. "
            "Returns a specific position for a customer on the given date."
        ),
        annotations=_READ,
    )
    async def get_customer_position_by_id(
        customer_id: Annotated[str, "Bank customer id (path customerId)"],
        position_id: Annotated[str, "Position id given by the bank"],
        date: Annotated[str, "Valuation date YYYY-MM-DD (required by OpenAPI)"],
        end_of_day_indicator: Annotated[bool | None, "Optional EOD filter"] = None,
    ) -> str:
        return await invoke_tool(
            "getCustomerPositionById",
            get_app().service.get_customer_position_by_id(
                customer_id,
                position_id,
                date,
                end_of_day_indicator=end_of_day_indicator,
            ),
        )

    @mcp.tool(
        name="get_account_position_by_account_id",
        description=(
            "OpenWealth Custody operationId=getAccountPositionByAccountId. "
            "Returns positions for an account on the given date."
        ),
        annotations=_READ,
    )
    async def get_account_position_by_account_id(
        account_id: Annotated[str, "Account id (not IBAN)"],
        date: Annotated[str, "Valuation date YYYY-MM-DD (required by OpenAPI)"],
        end_of_day_indicator: Annotated[bool | None, "Optional EOD filter"] = None,
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "getAccountPositionByAccountId",
            get_app().service.get_account_positions(
                account_id,
                date,
                end_of_day_indicator=end_of_day_indicator,
                cursor=cursor,
                limit=limit,
            ),
        )

    @mcp.tool(
        name="get_account_position_by_id",
        description=(
            "OpenWealth Custody operationId=getAccountPositionById. "
            "Returns a specific position for an account on the given date."
        ),
        annotations=_READ,
    )
    async def get_account_position_by_id(
        account_id: Annotated[str, "Account id (not IBAN)"],
        position_id: Annotated[str, "Position id given by the bank"],
        date: Annotated[str, "Valuation date YYYY-MM-DD (required by OpenAPI)"],
        end_of_day_indicator: Annotated[bool | None, "Optional EOD filter"] = None,
    ) -> str:
        return await invoke_tool(
            "getAccountPositionById",
            get_app().service.get_account_position_by_id(
                account_id,
                position_id,
                date,
                end_of_day_indicator=end_of_day_indicator,
            ),
        )

    @mcp.tool(
        name="get_transaction_by_customer_id",
        description=(
            "OpenWealth Custody operationId=getTransactionByCustomerId. "
            "Returns transactions for a customer on the given date."
        ),
        annotations=_READ,
    )
    async def get_transaction_by_customer_id(
        customer_id: Annotated[str, "Bank customer id (path customerId)"],
        date: Annotated[str, "Transaction date YYYY-MM-DD (required by OpenAPI)"],
        end_of_day_indicator: Annotated[bool | None, "Optional EOD filter"] = None,
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "getTransactionByCustomerId",
            get_app().service.get_customer_transactions(
                customer_id,
                date,
                end_of_day_indicator=end_of_day_indicator,
                cursor=cursor,
                limit=limit,
            ),
        )

    @mcp.tool(
        name="get_transaction_by_transaction_id",
        description=(
            "OpenWealth Custody operationId=getTransactionByTransactionId. "
            "Returns a specific transaction for a customer."
        ),
        annotations=_READ,
    )
    async def get_transaction_by_transaction_id(
        customer_id: Annotated[str, "Bank customer id (path customerId)"],
        transaction_id: Annotated[str, "Transaction id given by the bank"],
    ) -> str:
        return await invoke_tool(
            "getTransactionByTransactionId",
            get_app().service.get_transaction_by_id(customer_id, transaction_id),
        )
