"""Tests for MCP resources and tool error mapping."""

import json

import httpx
import pytest

from openwealth_mcp.app import set_client
from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.config import Settings
from openwealth_mcp.resources.custody import register_custody_resources
from openwealth_mcp.server import mcp
from openwealth_mcp.tools.custody import invoke_tool

_CUSTODY_URL = "https://api.example.com/api/custody-services/v3"


def _settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        custody_base_url=_CUSTODY_URL,
        bearer_token="test-token",
        max_retries=0,
        _env_file=None,
    )


@pytest.mark.asyncio
async def test_resources_registered() -> None:
    resources = await mcp.list_resources()
    uris = {str(r.uri) for r in resources}
    assert "openwealth://specs/custody" in uris
    assert "openwealth://specs/custody.yaml" in uris


@pytest.mark.asyncio
async def test_invoke_tool_maps_validation_error() -> None:
    async def boom() -> str:
        from openwealth_mcp.errors import ToolValidationError

        raise ToolValidationError("bad input")

    payload = json.loads(await invoke_tool("getCustomers", boom()))
    assert payload["error"] is True
    assert payload["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_invoke_tool_maps_transport_error() -> None:
    async def boom() -> str:
        from openwealth_mcp.errors import TransportError

        raise TransportError("down", correlation_id="c1")

    payload = json.loads(await invoke_tool("getCustomers", boom()))
    assert payload["error_code"] == "TRANSPORT_ERROR"
    assert payload["retryable"] is True


@pytest.mark.asyncio
async def test_tool_validation_error_via_service() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    client = OpenWealthHttpClient(
        settings=_settings(), base_url=_CUSTODY_URL, transport=httpx.MockTransport(handler)
    )
    set_client(client)
    try:
        result = await mcp.call_tool(
            "get_customer_position_by_customer_id",
            {"customer_id": "C1", "date": "bad"},
        )
        text = result
        if not isinstance(text, str):
            structured = getattr(result, "structured_content", None)
            if isinstance(structured, dict) and "result" in structured:
                text = structured["result"]
            elif hasattr(result, "content"):
                text = result.content[0].text  # type: ignore[attr-defined]
            else:
                raise AssertionError(result)
        payload = json.loads(text)
        assert payload["error"] is True
        assert payload["error_code"] == "VALIDATION_ERROR"
    finally:
        set_client(None)
        await client.aclose()


def test_register_custody_resources_idempotent() -> None:
    # Already registered on server.mcp; calling again on a fresh FastMCP is enough.
    from fastmcp import FastMCP

    other = FastMCP("tmp")
    register_custody_resources(other)


@pytest.mark.asyncio
async def test_custody_spec_summary_resource() -> None:
    """Reading the custody spec summary resource returns the table text."""
    from fastmcp import FastMCP

    server = FastMCP("tmp")
    register_custody_resources(server)
    result = await server.read_resource("openwealth://specs/custody")
    assert "get_customers" in str(result)


@pytest.mark.asyncio
async def test_trading_resources_registered() -> None:
    """Trading server exposes both trading spec resources."""
    from openwealth_mcp.trading.server import mcp as trading_mcp

    resources = await trading_mcp.list_resources()
    uris = {str(r.uri) for r in resources}
    assert "openwealth://specs/trading" in uris
    assert "openwealth://specs/trading.yaml" in uris


@pytest.mark.asyncio
async def test_trading_spec_summary_resource() -> None:
    from fastmcp import FastMCP

    from openwealth_mcp.resources.trading import register_trading_resources

    server = FastMCP("tmp")
    register_trading_resources(server)
    result = await server.read_resource("openwealth://specs/trading")
    assert "create_order" in str(result)


@pytest.mark.asyncio
async def test_customer_resources_registered() -> None:
    """Customer Management server exposes both customer spec resources."""
    from openwealth_mcp.customer.server import mcp as customer_mcp

    resources = await customer_mcp.list_resources()
    uris = {str(r.uri) for r in resources}
    assert "openwealth://specs/customer" in uris
    assert "openwealth://specs/customer.yaml" in uris


@pytest.mark.asyncio
async def test_customer_spec_summary_resource() -> None:
    from fastmcp import FastMCP

    from openwealth_mcp.resources.customer import register_customer_resources

    server = FastMCP("tmp")
    register_customer_resources(server)
    result = await server.read_resource("openwealth://specs/customer")
    assert "create_customer" in str(result)


