"""Contract-test the services against the vendored OpenAPI specs.

Each service method is paired with the operationId and path prefix it uses.
If a spec update removes or renames an operation, this test fails loudly
instead of silently returning 404s to the model.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_SPECS_DIR = Path(__file__).parents[1] / "specs"


def _load_spec(filename: str) -> dict:  # type: ignore[type-arg]
    path = _SPECS_DIR / filename
    return yaml.safe_load(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _operations(spec: dict) -> dict[str, str]:  # type: ignore[type-arg]
    """Return {operationId: path} for every GET/POST/PUT/DELETE in the spec."""
    result: dict[str, str] = {}
    for path, methods in spec.get("paths", {}).items():
        for _method, op in methods.items():
            if isinstance(op, dict) and "operationId" in op:
                result[op["operationId"]] = path
    return result


# ---------------------------------------------------------------------------
# Custody spec contract
# ---------------------------------------------------------------------------

CUSTODY_OPERATIONS = [
    ("getCustomers", "/customers"),
    ("getCustomersByCustomerId", "/customers/{customerId}"),
    ("getCustomerAccountsByCustomerId", "/customers/{customerId}/accounts"),
    ("getCustomerAccountById", "/customers/{customerId}/accounts/{accountId}"),
    ("getCustomerPositionByCustomerId", "/customers/{customerId}/positions"),
    ("getCustomerPositionById", "/customers/{customerId}/positions/{positionId}"),
    ("getAccountPositionByAccountId", "/accounts/{accountId}/positions"),
    ("getAccountPositionById", "/accounts/{accountId}/positions/{positionId}"),
    ("getTransactionByCustomerId", "/customers/{customerId}/transactions"),
    ("getTransactionByTransactionId", "/customers/{customerId}/transactions/{transactionId}"),
]


@pytest.mark.parametrize("operation_id,expected_path", CUSTODY_OPERATIONS)
def test_custody_operation_in_spec(operation_id: str, expected_path: str) -> None:
    spec = _load_spec("custodyAPI.yaml")
    ops = _operations(spec)
    assert operation_id in ops, (
        f"operationId '{operation_id}' not found in custodyAPI.yaml. "
        "The spec may have changed; update CustodyService or bump the spec."
    )
    assert ops[operation_id] == expected_path, (
        f"operationId '{operation_id}' has path '{ops[operation_id]}' in spec "
        f"but service uses '{expected_path}'."
    )


# ---------------------------------------------------------------------------
# Trading spec contract
# ---------------------------------------------------------------------------

TRADING_OPERATIONS = [
    ("listCustomers", "/customers"),
    ("getCustomer", "/customers/{customerId}"),
    ("listAccounts", "/accounts"),
    ("getAccount", "/accounts/{accountId}"),
    ("listOrders", "/orders"),
    ("getOrder", "/orders/{orderId}"),
    ("createOrder", "/orders"),
    ("actionCancelOrder", "/orders/{orderId}/actions/cancel"),
    ("listOrderExecutions", "/orders/{orderId}/executions"),
    ("getOrderExecution", "/orders/{orderId}/executions/{executionId}"),
    ("listOrderStates", "/orders/{orderId}/states"),
    ("createQuote", "/quotes"),
    ("listEventSubscriptions", "/event-subscriptions"),
    ("getEventSubscription", "/event-subscriptions/{eventSubscriptionId}"),
    ("createEventSubscription", "/event-subscriptions"),
    ("updateEventSubscription", "/event-subscriptions/{eventSubscriptionId}"),
    ("deleteEventSubscription", "/event-subscriptions/{eventSubscriptionId}"),
    (
        "listEventSubscriptionEventNotifications",
        "/event-subscriptions/{eventSubscriptionId}/event-notifications",
    ),
]


@pytest.mark.parametrize("operation_id,expected_path", TRADING_OPERATIONS)
def test_trading_operation_in_spec(operation_id: str, expected_path: str) -> None:
    spec = _load_spec("tradingAPI.yaml")
    ops = _operations(spec)
    assert operation_id in ops, (
        f"operationId '{operation_id}' not found in tradingAPI.yaml. "
        "The spec may have changed; update TradingService or bump the spec."
    )
    assert ops[operation_id] == expected_path, (
        f"operationId '{operation_id}' has path '{ops[operation_id]}' in spec "
        f"but service uses '{expected_path}'."
    )
