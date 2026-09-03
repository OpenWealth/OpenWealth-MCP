"""Backward-compat shim — custody app now lives in openwealth_mcp.custody.app."""

from __future__ import annotations

from openwealth_mcp.custody.app import get_custody_app as get_app
from openwealth_mcp.custody.app import set_custody_client as set_client

__all__ = ["get_app", "set_client"]
