"""Custody domain service — one method per OpenAPI operationId.

This layer owns all path construction and query-parameter assembly so that
the MCP tool adapters remain thin (one-liners).  It has no MCP or HTTP-
transport knowledge; it delegates every network call to ``OpenWealthHttpClient``.
"""

from __future__ import annotations

from urllib.parse import quote

from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.validation import validate_date, validate_id, validate_limit


def _seg(value: str) -> str:
    return quote(value, safe="")


class CustodyService:
    """Maps OpenWealth Custody operationIds to HTTP calls."""

    def __init__(self, client: OpenWealthHttpClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    async def get_customers(
        self,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        return await self._client.get(
            "/customers",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )

    async def get_customer_by_id(self, customer_id: str) -> str:
        cid = validate_id(customer_id, "customer_id")
        return await self._client.get(f"/customers/{_seg(cid)}")

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------

    async def get_customer_accounts(
        self,
        customer_id: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        cid = validate_id(customer_id, "customer_id")
        return await self._client.get(
            f"/customers/{_seg(cid)}/accounts",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )

    async def get_customer_account_by_id(
        self,
        customer_id: str,
        account_id: str,
    ) -> str:
        cid = validate_id(customer_id, "customer_id")
        aid = validate_id(account_id, "account_id")
        return await self._client.get(f"/customers/{_seg(cid)}/accounts/{_seg(aid)}")

    # ------------------------------------------------------------------
    # Positions (customer-level)
    # ------------------------------------------------------------------

    async def get_customer_positions(
        self,
        customer_id: str,
        date: str,
        *,
        end_of_day_indicator: bool | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        cid = validate_id(customer_id, "customer_id")
        return await self._client.get(
            f"/customers/{_seg(cid)}/positions",
            params={
                "date": validate_date(date),
                "end_of_day_indicator": end_of_day_indicator,
                "cursor": cursor,
                "limit": validate_limit(limit),
            },
        )

    async def get_customer_position_by_id(
        self,
        customer_id: str,
        position_id: str,
        date: str,
        *,
        end_of_day_indicator: bool | None = None,
    ) -> str:
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(position_id, "position_id")
        return await self._client.get(
            f"/customers/{_seg(cid)}/positions/{_seg(pid)}",
            params={
                "date": validate_date(date),
                "end_of_day_indicator": end_of_day_indicator,
            },
        )

    # ------------------------------------------------------------------
    # Positions (account-level)
    # ------------------------------------------------------------------

    async def get_account_positions(
        self,
        account_id: str,
        date: str,
        *,
        end_of_day_indicator: bool | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        aid = validate_id(account_id, "account_id")
        return await self._client.get(
            f"/accounts/{_seg(aid)}/positions",
            params={
                "date": validate_date(date),
                "end_of_day_indicator": end_of_day_indicator,
                "cursor": cursor,
                "limit": validate_limit(limit),
            },
        )

    async def get_account_position_by_id(
        self,
        account_id: str,
        position_id: str,
        date: str,
        *,
        end_of_day_indicator: bool | None = None,
    ) -> str:
        aid = validate_id(account_id, "account_id")
        pid = validate_id(position_id, "position_id")
        return await self._client.get(
            f"/accounts/{_seg(aid)}/positions/{_seg(pid)}",
            params={
                "date": validate_date(date),
                "end_of_day_indicator": end_of_day_indicator,
            },
        )

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    async def get_customer_transactions(
        self,
        customer_id: str,
        date: str,
        *,
        end_of_day_indicator: bool | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        cid = validate_id(customer_id, "customer_id")
        return await self._client.get(
            f"/customers/{_seg(cid)}/transactions",
            params={
                "date": validate_date(date),
                "end_of_day_indicator": end_of_day_indicator,
                "cursor": cursor,
                "limit": validate_limit(limit),
            },
        )

    async def get_transaction_by_id(
        self,
        customer_id: str,
        transaction_id: str,
    ) -> str:
        cid = validate_id(customer_id, "customer_id")
        tid = validate_id(transaction_id, "transaction_id")
        return await self._client.get(f"/customers/{_seg(cid)}/transactions/{_seg(tid)}")
