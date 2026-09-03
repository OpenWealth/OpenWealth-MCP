"""MCP server composition root for OpenWealth Trading (Order Placement) API."""

from __future__ import annotations

import sys

from fastmcp import FastMCP

from openwealth_mcp import __version__
from openwealth_mcp._server_base import build_server, run_stdio
from openwealth_mcp.config import get_settings
from openwealth_mcp.logging_config import setup_logging
from openwealth_mcp.resources.trading import register_trading_resources
from openwealth_mcp.tools.trading import register_trading_tools
from openwealth_mcp.trading.app import get_trading_app

_INSTRUCTIONS = (
    "OpenWealth Trading (Order Placement) API v3.0.1 MCP server. "
    "Use the tools to manage orders, query executions, request quotes, "
    "and manage event subscriptions. "
    "Configure OPENWEALTH_TRADING_BASE_URL and OPENWEALTH_BEARER_TOKEN before use. "
    "IMPORTANT: create_order places a real financial order — confirm all details before calling. "
    "Sandbox docs: "
    "https://sandbox.openwealth.synpulse8.com/docs?api=order-placement-3-0-1"
)


def create_trading_mcp() -> FastMCP:
    """Compose FastMCP with Trading tools and resources."""
    return build_server(
        name="openwealth-trading",
        instructions=_INSTRUCTIONS,
        register_tools=register_trading_tools,
        register_resources=register_trading_resources,
    )


mcp = create_trading_mcp()


def main() -> None:
    """Run the Trading MCP server over stdio.

    Pass ``--check`` as the first argument to validate settings and exit
    without starting the server (useful for deployment smoke tests).
    """
    check_only = len(sys.argv) > 1 and sys.argv[1] == "--check"

    settings = get_settings()
    log = setup_logging(settings.log_level, log_file=settings.log_file)
    if not settings.verify_tls:
        log.warning("TLS verification disabled (OPENWEALTH_VERIFY_TLS=false)")

    try:
        base_url = settings.base_url_for("trading")
    except ValueError as exc:
        log.error("%s", exc)
        raise SystemExit(1) from exc

    log.info(
        "openwealth-trading v%s base_url=%s auth_configured=yes log_level=%s log_file=%s",
        __version__,
        base_url,
        settings.log_level,
        settings.log_file or "(stderr only)",
    )

    if check_only:
        print(f"OK openwealth-trading v{__version__} base_url={base_url}")
        return

    # create_trading_mcp and get_trading_app are resolved at runtime so test patches work.
    server = create_trading_mcp()
    _ = get_trading_app().client
    run_stdio("openwealth-trading", server, get_trading_app, log)


if __name__ == "__main__":
    main()
