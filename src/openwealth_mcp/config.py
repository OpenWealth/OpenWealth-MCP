"""Runtime configuration for the OpenWealth MCP server."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings. Host and auth are never hard-coded.

    Each MCP server now has its own base URL:

    - ``OPENWEALTH_CUSTODY_BASE_URL`` — required when running the Custody server.
    - ``OPENWEALTH_TRADING_BASE_URL`` — required when running the Trading server.

    Both fields are optional at model-validation time so that a single ``.env``
    file can serve both servers without each server rejecting the other's URL.
    The ``base_url_for(service)`` method raises a clear ``ValueError`` when the
    URL needed by a specific server is absent.
    """

    model_config = SettingsConfigDict(
        env_prefix="OPENWEALTH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    custody_base_url: str | None = Field(
        default=None,
        description=(
            "Custody API base URL including path prefix, no trailing slash. "
            "Required when running the Custody MCP server."
        ),
    )
    trading_base_url: str | None = Field(
        default=None,
        description=(
            "Trading API base URL including path prefix, no trailing slash. "
            "Required when running the Trading MCP server."
        ),
    )
    customer_management_base_url: str | None = Field(
        default=None,
        description=(
            "Customer Management API base URL including path prefix, no trailing slash. "
            "Required when running the Customer Management MCP server."
        ),
    )
    bearer_token: str | None = Field(default=None)
    auth_header: str | None = Field(
        default=None,
        description="Full Authorization header value (overrides bearer_token).",
    )
    correlation_id: str | None = Field(
        default=None,
        description="Fixed X-Correlation-ID; if unset, generated per request.",
    )
    timeout_seconds: float = Field(default=120.0, gt=0, le=300)
    connect_timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    max_retries: int = Field(default=2, ge=0, le=5)
    verify_tls: bool = Field(default=True)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_file: str | None = Field(
        default=None,
        description="Optional log file path (also logs to stderr).",
    )

    @field_validator(
        "custody_base_url", "trading_base_url", "customer_management_base_url", mode="before"
    )
    @classmethod
    def normalize_base_url(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        url = value.strip().rstrip("/")
        if url and not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        return url or None

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value

    @model_validator(mode="after")
    def require_auth(self) -> Self:
        if not self.authorization_header():
            raise ValueError("OPENWEALTH_BEARER_TOKEN or OPENWEALTH_AUTH_HEADER is required")
        return self

    def authorization_header(self) -> str | None:
        if self.auth_header:
            return self.auth_header
        if self.bearer_token:
            token = self.bearer_token
            if token.lower().startswith("bearer "):
                return token
            return f"Bearer {token}"
        return None

    def base_url_for(self, service: Literal["custody", "trading", "customer"]) -> str:
        """Return the base URL for the given service, raising if not configured."""
        _url_map: dict[str, str | None] = {
            "custody": self.custody_base_url,
            "trading": self.trading_base_url,
            "customer": self.customer_management_base_url,
        }
        url = _url_map[service]
        if not url:
            env_var_map: dict[str, str] = {
                "custody": "OPENWEALTH_CUSTODY_BASE_URL",
                "trading": "OPENWEALTH_TRADING_BASE_URL",
                "customer": "OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL",
            }
            raise ValueError(f"{env_var_map[service]} is required but not set")
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
