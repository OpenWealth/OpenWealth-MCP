"""Smoke-test the server entry points.

Covers both ``main()`` paths (normal start and ``--check``) with
``server.run`` monkeypatched so no real stdio MCP loop is started.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Custody server
# ---------------------------------------------------------------------------


def test_custody_main_check_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """``--check`` should print an OK line and return without starting the server."""
    with (
        patch.object(sys, "argv", ["openwealth-custody-mcp", "--check"]),
        patch("openwealth_mcp.custody.server.create_custody_mcp") as mock_create,
    ):
        from openwealth_mcp.custody.server import main

        main()

    out = capsys.readouterr().out
    assert out.startswith("OK openwealth-custody")
    mock_create.assert_not_called()


def test_custody_main_runs_server() -> None:
    """Normal invocation should call ``server.run(transport='stdio')``."""
    mock_server = MagicMock()
    with (
        patch.object(sys, "argv", ["openwealth-custody-mcp"]),
        patch("openwealth_mcp.custody.server.create_custody_mcp", return_value=mock_server),
        patch("openwealth_mcp.custody.server.get_custody_app") as mock_get_app,
    ):
        mock_get_app.return_value.client = MagicMock()
        from openwealth_mcp.custody.server import main

        main()

    mock_server.run.assert_called_once_with(transport="stdio", show_banner=False)


def test_custody_main_missing_url_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() exits with SystemExit when OPENWEALTH_CUSTODY_BASE_URL is unset."""
    from openwealth_mcp.config import get_settings

    monkeypatch.delenv("OPENWEALTH_CUSTODY_BASE_URL", raising=False)
    get_settings.cache_clear()
    with (
        patch.object(sys, "argv", ["openwealth-custody-mcp"]),
        pytest.raises(SystemExit),
    ):
        from openwealth_mcp.custody.server import main

        main()
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Trading server
# ---------------------------------------------------------------------------


def test_trading_main_check_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """``--check`` should print an OK line and return without starting the server."""
    with (
        patch.object(sys, "argv", ["openwealth-trading-mcp", "--check"]),
        patch("openwealth_mcp.trading.server.create_trading_mcp") as mock_create,
    ):
        from openwealth_mcp.trading.server import main

        main()

    out = capsys.readouterr().out
    assert out.startswith("OK openwealth-trading")
    mock_create.assert_not_called()


def test_trading_main_missing_url_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() exits with SystemExit when OPENWEALTH_TRADING_BASE_URL is unset."""
    from openwealth_mcp.config import get_settings

    monkeypatch.delenv("OPENWEALTH_TRADING_BASE_URL", raising=False)
    get_settings.cache_clear()
    with (
        patch.object(sys, "argv", ["openwealth-trading-mcp"]),
        pytest.raises(SystemExit),
    ):
        from openwealth_mcp.trading.server import main

        main()
    get_settings.cache_clear()


def test_trading_main_runs_server() -> None:
    """Normal invocation should call ``server.run(transport='stdio')``."""
    mock_server = MagicMock()
    with (
        patch.object(sys, "argv", ["openwealth-trading-mcp"]),
        patch("openwealth_mcp.trading.server.create_trading_mcp", return_value=mock_server),
        patch("openwealth_mcp.trading.server.get_trading_app") as mock_get_app,
    ):
        mock_get_app.return_value.client = MagicMock()
        from openwealth_mcp.trading.server import main

        main()

    mock_server.run.assert_called_once_with(transport="stdio", show_banner=False)


# ---------------------------------------------------------------------------
# Retry-After and jitter in client
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Customer Management server
# ---------------------------------------------------------------------------


def test_customer_main_check_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """``--check`` should print an OK line and return without starting the server."""
    with (
        patch.object(sys, "argv", ["openwealth-customer-mcp", "--check"]),
        patch("openwealth_mcp.customer.server.create_customer_mcp") as mock_create,
    ):
        from openwealth_mcp.customer.server import main

        main()

    out = capsys.readouterr().out
    assert out.startswith("OK openwealth-customer")
    mock_create.assert_not_called()


def test_customer_main_missing_url_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() exits with SystemExit when OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL is unset."""
    from openwealth_mcp.config import get_settings

    monkeypatch.delenv("OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL", raising=False)
    get_settings.cache_clear()
    with (
        patch.object(sys, "argv", ["openwealth-customer-mcp"]),
        pytest.raises(SystemExit),
    ):
        from openwealth_mcp.customer.server import main

        main()
    get_settings.cache_clear()


def test_customer_main_runs_server() -> None:
    """Normal invocation should call ``server.run(transport='stdio')``."""
    mock_server = MagicMock()
    with (
        patch.object(sys, "argv", ["openwealth-customer-mcp"]),
        patch("openwealth_mcp.customer.server.create_customer_mcp", return_value=mock_server),
        patch("openwealth_mcp.customer.server.get_customer_app") as mock_get_app,
    ):
        mock_get_app.return_value.client = MagicMock()
        from openwealth_mcp.customer.server import main

        main()

    mock_server.run.assert_called_once_with(transport="stdio", show_banner=False)


# ---------------------------------------------------------------------------
# Retry-After and jitter in client
# ---------------------------------------------------------------------------


def test_backoff_honours_retry_after_seconds() -> None:
    """_backoff_seconds should use the Retry-After header value (in seconds)."""
    from openwealth_mcp.client import _backoff_seconds

    response = MagicMock()
    response.headers.get.return_value = "10"
    delay = _backoff_seconds(1, response=response)
    assert 8.0 <= delay <= 12.0, f"Expected jittered ≈10s, got {delay}"


def test_backoff_falls_back_to_exponential_without_header() -> None:
    """Without a Retry-After header _backoff_seconds uses exponential backoff."""
    from openwealth_mcp.client import _backoff_seconds

    delay1 = _backoff_seconds(1, response=None)
    delay2 = _backoff_seconds(2, response=None)
    assert 0.2 <= delay1 <= 0.3, f"attempt 1 expected ≈0.25s, got {delay1}"
    assert 0.4 <= delay2 <= 0.6, f"attempt 2 expected ≈0.5s, got {delay2}"


def test_backoff_jitter_range() -> None:
    """_jitter should stay within ±20 % of the input."""
    from openwealth_mcp.client import _jitter

    samples = [_jitter(1.0) for _ in range(200)]
    assert all(0.8 <= s <= 1.2 for s in samples), "jitter outside ±20% band"
