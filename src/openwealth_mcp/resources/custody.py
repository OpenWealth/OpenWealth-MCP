"""MCP resource providers for OpenWealth Custody Services.

Keeps filesystem I/O and static content out of ``server.py``.
"""

from __future__ import annotations

from fastmcp import FastMCP

from openwealth_mcp.resources._spec_path import resolve_spec_path

_SPEC_SUMMARY = """\
# OpenWealth Custody Services API v3.2.0

Docs: https://sandbox.openwealth.synpulse8.com/docs?api=custody-services-3-2-0
Spec: specs/custodyAPI.yaml (vendored)

| Tool | operationId | Method path |
|------|-------------|-------------|
| get_customers | getCustomers | GET /customers |
| get_customers_by_customer_id | getCustomersByCustomerId | GET /customers/{customerId} |
| get_customer_accounts_by_customer_id | getCustomerAccountsByCustomerId | GET /customers/{customerId}/accounts |
| get_customer_account_by_id | getCustomerAccountById | GET /customers/{customerId}/accounts/{accountId} |
| get_customer_position_by_customer_id | getCustomerPositionByCustomerId | GET /customers/{customerId}/positions |
| get_customer_position_by_id | getCustomerPositionById | GET /customers/{customerId}/positions/{positionId} |
| get_account_position_by_account_id | getAccountPositionByAccountId | GET /accounts/{accountId}/positions |
| get_account_position_by_id | getAccountPositionById | GET /accounts/{accountId}/positions/{positionId} |
| get_transaction_by_customer_id | getTransactionByCustomerId | GET /customers/{customerId}/transactions |
| get_transaction_by_transaction_id | getTransactionByTransactionId | GET /customers/{customerId}/transactions/{transactionId} |
"""

_SPEC_NOT_FOUND = "custodyAPI.yaml not found; ensure specs/custodyAPI.yaml is present."


def register_custody_resources(mcp: FastMCP) -> None:
    """Register Custody spec resources on the MCP server."""

    @mcp.resource("openwealth://specs/custody")
    def custody_spec_summary() -> str:
        """Summary of Custody Services v3.2.0 endpoints exposed as tools."""
        return _SPEC_SUMMARY

    @mcp.resource("openwealth://specs/custody.yaml")
    def custody_spec_yaml() -> str:
        """Vendored OpenAPI YAML for Custody Services v3.2.0."""
        path = resolve_spec_path("custodyAPI.yaml")
        if path is None:
            return _SPEC_NOT_FOUND
        return path.read_text(encoding="utf-8")
