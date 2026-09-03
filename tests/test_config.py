"""Tests for configuration loading."""

import pytest
from pydantic import ValidationError

from openwealth_mcp.config import Settings, get_settings


def test_custody_url_strips_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "OPENWEALTH_CUSTODY_BASE_URL",
        "https://api.example.com/api/custody-services/v3/",
    )
    monkeypatch.setenv("OPENWEALTH_BEARER_TOKEN", "tok")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.custody_base_url == "https://api.example.com/api/custody-services/v3"
    assert settings.authorization_header() == "Bearer tok"
    get_settings.cache_clear()


def test_trading_url_strips_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "OPENWEALTH_TRADING_BASE_URL",
        "https://api.example.com/api/trading-services/v1/",
    )
    monkeypatch.setenv("OPENWEALTH_BEARER_TOKEN", "tok")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.trading_base_url == "https://api.example.com/api/trading-services/v1"


def test_custody_url_adds_https_scheme(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENWEALTH_CUSTODY_BASE_URL", "api.example.com/v3")
    monkeypatch.setenv("OPENWEALTH_BEARER_TOKEN", "tok")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.custody_base_url == "https://api.example.com/v3"


def test_auth_header_overrides_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENWEALTH_BEARER_TOKEN", "ignored")
    monkeypatch.setenv("OPENWEALTH_AUTH_HEADER", "Bearer custom")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.authorization_header() == "Bearer custom"


def test_settings_valid_without_any_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings itself is valid even with no URLs; servers fail on startup instead."""
    monkeypatch.delenv("OPENWEALTH_CUSTODY_BASE_URL", raising=False)
    monkeypatch.delenv("OPENWEALTH_TRADING_BASE_URL", raising=False)
    monkeypatch.setenv("OPENWEALTH_BEARER_TOKEN", "tok")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.custody_base_url is None
    assert settings.trading_base_url is None


def test_base_url_for_custody_returns_url() -> None:
    settings = Settings(  # type: ignore[call-arg]
        custody_base_url="https://custody.example.com/v3",
        trading_base_url=None,
        bearer_token="tok",
        _env_file=None,
    )
    assert settings.base_url_for("custody") == "https://custody.example.com/v3"


def test_base_url_for_trading_returns_url() -> None:
    settings = Settings(  # type: ignore[call-arg]
        custody_base_url=None,
        trading_base_url="https://trading.example.com/v1",
        bearer_token="tok",
        _env_file=None,
    )
    assert settings.base_url_for("trading") == "https://trading.example.com/v1"


def test_base_url_for_custody_missing_raises() -> None:
    settings = Settings(  # type: ignore[call-arg]
        custody_base_url=None,
        bearer_token="tok",
        _env_file=None,
    )
    with pytest.raises(ValueError, match="OPENWEALTH_CUSTODY_BASE_URL"):
        settings.base_url_for("custody")


def test_base_url_for_trading_missing_raises() -> None:
    settings = Settings(  # type: ignore[call-arg]
        trading_base_url=None,
        bearer_token="tok",
        _env_file=None,
    )
    with pytest.raises(ValueError, match="OPENWEALTH_TRADING_BASE_URL"):
        settings.base_url_for("trading")


def test_normalize_base_url_handles_empty_string() -> None:
    """An empty string URL is normalised to None (not stored as an empty string)."""
    settings = Settings(  # type: ignore[call-arg]
        custody_base_url="",
        bearer_token="tok",
        _env_file=None,
    )
    assert settings.custody_base_url is None


def test_customer_management_url_strips_trailing_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL",
        "https://api.example.com/api/customer-management/v2/",
    )
    monkeypatch.setenv("OPENWEALTH_BEARER_TOKEN", "tok")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert (
        settings.customer_management_base_url
        == "https://api.example.com/api/customer-management/v2"
    )


def test_base_url_for_customer_returns_url() -> None:
    settings = Settings(  # type: ignore[call-arg]
        customer_management_base_url="https://customer.example.com/v2",
        bearer_token="tok",
        _env_file=None,
    )
    assert settings.base_url_for("customer") == "https://customer.example.com/v2"


def test_base_url_for_customer_missing_raises() -> None:
    settings = Settings(  # type: ignore[call-arg]
        customer_management_base_url=None,
        bearer_token="tok",
        _env_file=None,
    )
    with pytest.raises(ValueError, match="OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL"):
        settings.base_url_for("customer")


def test_missing_auth_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENWEALTH_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("OPENWEALTH_AUTH_HEADER", raising=False)
    with pytest.raises(ValidationError, match="BEARER_TOKEN|AUTH_HEADER"):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_bearer_token_without_prefix_is_prefixed() -> None:
    settings = Settings(  # type: ignore[call-arg]
        bearer_token="rawtoken",
        _env_file=None,
    )
    assert settings.authorization_header() == "Bearer rawtoken"


def test_bearer_token_with_prefix_is_unchanged() -> None:
    settings = Settings(  # type: ignore[call-arg]
        bearer_token="Bearer mytoken",
        _env_file=None,
    )
    assert settings.authorization_header() == "Bearer mytoken"
