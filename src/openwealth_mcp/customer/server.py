"""MCP server composition root for OpenWealth Customer Management API v2.0.6."""

from __future__ import annotations

import sys

from fastmcp import FastMCP

from openwealth_mcp import __version__
from openwealth_mcp._server_base import build_server, run_stdio
from openwealth_mcp.config import get_settings
from openwealth_mcp.customer.app import get_customer_app
from openwealth_mcp.logging_config import setup_logging
from openwealth_mcp.resources.customer import register_customer_resources
from openwealth_mcp.tools.customer import register_customer_tools

_INSTRUCTIONS = (
    "OpenWealth Customer Management API v2.0.6 MCP server. "
    "Use the tools to manage customer master data, persons, contacts, addresses, "
    "documents and KYC records, and to run prospect pre-checks. "
    "Configure OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL and OPENWEALTH_BEARER_TOKEN before use. "
    "IMPORTANT: create_customer, create_kyc and create_document mutate live customer data "
    "at the custody bank — confirm all details before calling write tools. "
    "Sandbox docs: "
    "https://sandbox.openwealth.synpulse8.com/docs?api=customer-management-2-0-6"
)


def create_customer_mcp() -> FastMCP:
    """Compose FastMCP with Customer Management tools and resources."""
    return build_server(
        name="openwealth-customer",
        instructions=_INSTRUCTIONS,
        register_tools=register_customer_tools,
        register_resources=register_customer_resources,
    )


mcp = create_customer_mcp()


def main() -> None:
    """Run the Customer Management MCP server over stdio.

    Pass ``--check`` as the first argument to validate settings and exit
    without starting the server (useful for deployment smoke tests).
    """
    check_only = len(sys.argv) > 1 and sys.argv[1] == "--check"

    settings = get_settings()
    log = setup_logging(settings.log_level, log_file=settings.log_file)
    if not settings.verify_tls:
        log.warning("TLS verification disabled (OPENWEALTH_VERIFY_TLS=false)")

    try:
        base_url = settings.base_url_for("customer")
    except ValueError as exc:
        log.error("%s", exc)
        raise SystemExit(1) from exc

    log.info(
        "openwealth-customer v%s base_url=%s auth_configured=yes log_level=%s log_file=%s",
        __version__,
        base_url,
        settings.log_level,
        settings.log_file or "(stderr only)",
    )

    if check_only:
        print(f"OK openwealth-customer v{__version__} base_url={base_url}")
        return

    # create_customer_mcp and get_customer_app are resolved at runtime so test patches work.
    server = create_customer_mcp()
    _ = get_customer_app().client
    run_stdio("openwealth-customer", server, get_customer_app, log)


if __name__ == "__main__":
    main()
