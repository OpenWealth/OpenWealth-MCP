"""Application container for the Customer Management MCP server."""

from __future__ import annotations

from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.customer.service import CustomerService
from openwealth_mcp.service_app import ServiceApp

CustomerApp = ServiceApp[CustomerService]


def _customer_url() -> str:
    from openwealth_mcp.config import get_settings  # deferred to avoid circular import

    return get_settings().base_url_for("customer")


_app: CustomerApp = ServiceApp(CustomerService, url_resolver=_customer_url)


def get_customer_app() -> CustomerApp:
    return _app


def set_customer_client(client: OpenWealthHttpClient | None) -> None:
    """Convenience shim for tests."""
    _app.set_client(client)
