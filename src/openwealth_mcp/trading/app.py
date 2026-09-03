"""Application container for the Trading MCP server."""

from __future__ import annotations

from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.service_app import ServiceApp
from openwealth_mcp.trading.service import TradingService

# Public type alias kept for backwards compat with any code that checks the type.
TradingApp = ServiceApp[TradingService]


def _trading_url() -> str:
    from openwealth_mcp.config import get_settings  # deferred to avoid circular import

    return get_settings().base_url_for("trading")


_app: TradingApp = ServiceApp(TradingService, url_resolver=_trading_url)


def get_trading_app() -> TradingApp:
    return _app


def set_trading_client(client: OpenWealthHttpClient | None) -> None:
    """Convenience shim for tests."""
    _app.set_client(client)
