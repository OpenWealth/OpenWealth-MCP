"""Backward-compat shim — custody server now lives in openwealth_mcp.custody.server."""

from __future__ import annotations

from openwealth_mcp.custody.server import create_custody_mcp as create_mcp
from openwealth_mcp.custody.server import main, mcp

__all__ = ["create_mcp", "main", "mcp"]
