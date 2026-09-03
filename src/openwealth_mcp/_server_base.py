"""Shared helpers for MCP server entry points.

Both ``server.py`` (Custody) and ``trading/server.py`` (Trading) use
``build_server`` to compose their FastMCP instance and ``run_stdio`` to
execute the stdio loop with atexit cleanup.

``main()`` in each server module keeps direct references to ``create_mcp``
and ``get_app`` so that test patches applied to those names continue to work.
"""

from __future__ import annotations

import asyncio
import atexit
import contextlib
import logging
from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP

from openwealth_mcp import __version__


def build_server(
    name: str,
    instructions: str,
    register_tools: Callable[[FastMCP], None],
    register_resources: Callable[[FastMCP], None],
) -> FastMCP:
    """Compose a FastMCP server with tools and resources registered."""
    server = FastMCP(
        name=name,
        version=__version__,
        instructions=instructions,
    )
    register_tools(server)
    register_resources(server)
    return server


def run_stdio(
    server_name: str,
    server: FastMCP,
    app_getter: Callable[[], Any],
    log: logging.Logger,
) -> None:
    """Register atexit cleanup, log startup, then run the server over stdio.

    ``app_getter`` is resolved from the caller's module namespace at the time
    ``main()`` is invoked, so test patches on e.g. ``server.get_app`` are
    still honoured.
    """

    def _close() -> None:
        with contextlib.suppress(Exception):
            asyncio.run(app_getter().aclose())

    atexit.register(_close)
    log.info("Starting %s over stdio", server_name)
    server.run(transport="stdio", show_banner=False)
