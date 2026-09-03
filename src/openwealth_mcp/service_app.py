"""Generic DI container shared by the Custody and Trading MCP servers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from openwealth_mcp.client import OpenWealthHttpClient

ServiceT = TypeVar("ServiceT")


class ServiceApp(Generic[ServiceT]):
    """Lightweight generic DI container for an MCP server.

    Wires ``OpenWealthHttpClient`` and a service together so that MCP tools
    never reach ``get_settings()`` directly and are straightforward to swap in
    tests.

    Usage (production)::

        app = ServiceApp(MyService, url_resolver=lambda: settings.base_url_for("custody"))
        service = app.service           # MyService bound to the client

    Usage (tests)::

        app = ServiceApp(MyService, url_resolver=lambda: "https://...")
        app.set_client(OpenWealthHttpClient(settings=..., base_url=..., transport=mock))
    """

    def __init__(
        self,
        service_factory: Callable[[OpenWealthHttpClient], ServiceT],
        client: OpenWealthHttpClient | None = None,
        *,
        url_resolver: Callable[[], str] | None = None,
    ) -> None:
        self._service_factory = service_factory
        self._client = client
        self._url_resolver = url_resolver
        self._service: ServiceT | None = None

    @property
    def client(self) -> OpenWealthHttpClient:
        if self._client is None:
            from openwealth_mcp.config import get_settings  # deferred to avoid circular imports

            settings = get_settings()
            if self._url_resolver is None:
                raise TypeError(
                    "ServiceApp requires a url_resolver to create the HTTP client. "
                    "Pass url_resolver=lambda: settings.base_url_for('<service>') "
                    "or inject a client via set_client()."
                )
            self._client = OpenWealthHttpClient(
                settings=settings,
                base_url=self._url_resolver(),
            )
        return self._client

    def set_client(self, client: OpenWealthHttpClient | None) -> None:
        """Replace the shared client; pass ``None`` to reset to lazy default."""
        self._client = client
        self._service = None

    @property
    def service(self) -> ServiceT:
        if self._service is None:
            self._service = self._service_factory(self.client)
        return self._service

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
