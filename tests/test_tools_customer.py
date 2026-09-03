"""Tests for Customer Management MCP tool adapters and error mapping."""

import json

import httpx
import pytest

from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.config import Settings
from openwealth_mcp.customer.app import set_customer_client
from openwealth_mcp.customer.server import mcp
from openwealth_mcp.tools.customer import invoke_tool


def _tool_text(result: object) -> str:
    """Extract the text payload from a call_tool result regardless of FastMCP version."""
    if isinstance(result, str):
        return result
    if hasattr(result, "content"):
        for part in result.content:  # type: ignore[attr-defined]
            if hasattr(part, "text"):
                return part.text  # type: ignore[attr-defined]
    if isinstance(result, list):
        for part in result:
            if hasattr(part, "text"):
                return part.text  # type: ignore[attr-defined]
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict) and "result" in structured:
        return structured["result"]  # type: ignore[no-any-return]
    return str(result)


_CUSTOMER_URL = "https://api.example.com/api/customer-management/v2"


def _settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        customer_management_base_url=_CUSTOMER_URL,
        bearer_token="test-token",
        max_retries=0,
        _env_file=None,
    )


def _inject(handler) -> OpenWealthHttpClient:  # type: ignore[type-arg]
    client = OpenWealthHttpClient(
        settings=_settings(),
        base_url=_CUSTOMER_URL,
        transport=httpx.MockTransport(handler),
    )
    set_customer_client(client)
    return client


# ---------------------------------------------------------------------------
# invoke_tool error mapping
# ---------------------------------------------------------------------------


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
async def test_invoke_tool_maps_api_error() -> None:
    async def boom() -> str:
        from openwealth_mcp.errors import OpenWealthApiError

        raise OpenWealthApiError(
            status_code=404,
            message="Customer not found",
            correlation_id="c2",
        )

    payload = json.loads(await invoke_tool("getCustomerByCustomerId", boom()))
    assert payload["error"] is True
    assert "404" in payload["error_code"]
    assert payload["retryable"] is False


# ---------------------------------------------------------------------------
# Tool registration smoke tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_customer_tools_registered() -> None:
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    expected = {
        "get_customers",
        "create_customer",
        "get_customer",
        "get_customer_details",
        "get_persons",
        "create_person",
        "get_person",
        "get_person_details",
        "get_contacts",
        "create_contact",
        "get_contact",
        "update_contact",
        "delete_contact",
        "get_addresses",
        "create_address",
        "get_address",
        "update_address",
        "get_documents",
        "create_document",
        "get_document",
        "get_document_details",
        "get_kyc",
        "create_kyc",
        "create_prospect_precheck",
        "get_prospect_precheck",
        "get_status",
    }
    assert expected.issubset(names)


@pytest.mark.asyncio
async def test_customer_resources_registered() -> None:
    resources = await mcp.list_resources()
    uris = {str(r.uri) for r in resources}
    assert "openwealth://specs/customer" in uris
    assert "openwealth://specs/customer.yaml" in uris


@pytest.mark.asyncio
async def test_customer_spec_yaml_resource_returns_yaml() -> None:
    from fastmcp import FastMCP

    from openwealth_mcp.resources.customer import register_customer_resources

    server = FastMCP("tmp-customer")
    register_customer_resources(server)
    result = await server.read_resource("openwealth://specs/customer")
    assert "get_customers" in str(result)


# ---------------------------------------------------------------------------
# Full round-trip via mcp.call_tool
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_customers_tool_returns_data() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"customerId": "C1"}])

    client = _inject(handler)
    try:
        result = await mcp.call_tool("get_customers", {})
        payload = json.loads(_tool_text(result))
        assert payload["data"][0]["customerId"] == "C1"
    finally:
        set_customer_client(None)
        await client.aclose()


@pytest.mark.asyncio
async def test_get_customer_tool_bad_id_returns_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = _inject(handler)
    try:
        result = await mcp.call_tool("get_customer", {"customer_id": ""})
        payload = json.loads(_tool_text(result))
        assert payload["error"] is True
    finally:
        set_customer_client(None)
        await client.aclose()


@pytest.mark.asyncio
async def test_delete_contact_tool() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        return httpx.Response(204, text="")

    client = _inject(handler)
    try:
        await mcp.call_tool(
            "delete_contact",
            {"customer_id": "C1", "person_id": "P1", "contact_id": "CO1"},
        )
    finally:
        set_customer_client(None)
        await client.aclose()
