"""Application container — wires client, service, and configuration together.

Centralises the creation of the shared ``OpenWealthHttpClient`` so that the
``CustodyService`` and MCP tools never reach out to ``get_settings()``
themselves and are straightforward to swap in tests.
"""

from __future__ import annotations

from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.custody.service import CustodyService
from openwealth_mcp.service_app import ServiceApp

# Public type alias kept for backwards compat with any code that checks the type.
CustodyApp = ServiceApp[CustodyService]


def _custody_url() -> str:
    from openwealth_mcp.config import get_settings  # deferred to avoid circular import

    return get_settings().base_url_for("custody")


_app: CustodyApp = ServiceApp(CustodyService, url_resolver=_custody_url)


def get_app() -> CustodyApp:
    return _app


def set_client(client: OpenWealthHttpClient | None) -> None:
    """Convenience shim for tests: ``from openwealth_mcp.app import set_client``."""
    _app.set_client(client)
