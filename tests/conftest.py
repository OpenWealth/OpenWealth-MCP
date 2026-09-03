"""Shared pytest fixtures for OpenWealth MCP tests."""

from __future__ import annotations

import pytest

from openwealth_mcp.config import get_settings


@pytest.fixture(autouse=True)
def _openwealth_default_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide minimal Settings so tool tests need not set process env.

    OPENWEALTH_BEARER_TOKEN is always required.
    Per-service URLs are set so that Custody, Trading and Customer tests work
    without additional env configuration.
    Individual tests may override these via their own monkeypatch.
    """
    monkeypatch.setenv(
        "OPENWEALTH_CUSTODY_BASE_URL",
        "https://api.example.com/api/custody-services/v3",
    )
    monkeypatch.setenv(
        "OPENWEALTH_TRADING_BASE_URL",
        "https://api.example.com/api/trading-services/v1",
    )
    monkeypatch.setenv(
        "OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL",
        "https://api.example.com/api/customer-management/v2",
    )
    monkeypatch.setenv("OPENWEALTH_BEARER_TOKEN", "test-token")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
