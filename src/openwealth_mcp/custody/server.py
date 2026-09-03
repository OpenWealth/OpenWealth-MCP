"""MCP server composition root for OpenWealth Custody Services API v3.2.0."""

from __future__ import annotations

import sys

from fastmcp import FastMCP

from openwealth_mcp import __version__
from openwealth_mcp._server_base import build_server, run_stdio
from openwealth_mcp.config import get_settings
from openwealth_mcp.custody.app import get_custody_app
from openwealth_mcp.logging_config import setup_logging
from openwealth_mcp.resources import register_custody_resources
from openwealth_mcp.tools import register_custody_tools

_INSTRUCTIONS = (
    "OpenWealth Custody Services API v3.2.0 MCP server. "
    "Use the get_* tools to query customers, accounts, positions, and transactions. "
    "Configure OPENWEALTH_CUSTODY_BASE_URL and OPENWEALTH_BEARER_TOKEN before use. "
    "Sandbox docs: "
    "https://sandbox.openwealth.synpulse8.com/docs?api=custody-services-3-2-0"
)


def create_custody_mcp() -> FastMCP:
    """Compose FastMCP with Custody tools and resources."""
    return build_server(
        name="openwealth-custody",
        instructions=_INSTRUCTIONS,
        register_tools=register_custody_tools,
        register_resources=register_custody_resources,
    )


# Module-level instance for imports and unit tests.
mcp = create_custody_mcp()


def main() -> None:
    """Run the Custody MCP server over stdio.

    Pass ``--check`` as the first argument to validate settings and exit
    without starting the server (useful for deployment smoke tests).
    """
    check_only = len(sys.argv) > 1 and sys.argv[1] == "--check"

    settings = get_settings()
    log = setup_logging(settings.log_level, log_file=settings.log_file)
    if not settings.verify_tls:
        log.warning("TLS verification disabled (OPENWEALTH_VERIFY_TLS=false)")

    try:
        base_url = settings.base_url_for("custody")
    except ValueError as exc:
        log.error("%s", exc)
        raise SystemExit(1) from exc

    log.info(
        "openwealth-custody v%s base_url=%s auth_configured=yes log_level=%s log_file=%s",
        __version__,
        base_url,
        settings.log_level,
        settings.log_file or "(stderr only)",
    )

    if check_only:
        print(f"OK openwealth-custody v{__version__} base_url={base_url}")
        return

    # create_custody_mcp and get_custody_app are resolved at runtime so test patches work.
    server = create_custody_mcp()
    _ = get_custody_app().client
    run_stdio("openwealth-custody", server, get_custody_app, log)


if __name__ == "__main__":
    main()
