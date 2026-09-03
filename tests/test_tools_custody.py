"""Custody tool registration and invocation tests."""

import json

import httpx
import pytest

from openwealth_mcp.app import set_client
from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.config import Settings
from openwealth_mcp.server import mcp

_CUSTODY_URL = "https://api.example.com/api/custody-services/v3"


def _settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        custody_base_url=_CUSTODY_URL,
        bearer_token="test-token",
        correlation_id="tool-cid",
        max_retries=0,
        _env_file=None,
    )


@pytest.mark.asyncio
async def test_tools_registered() -> None:
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    expected = {
        "get_customers",
        "get_customers_by_customer_id",
        "get_customer_accounts_by_customer_id",
        "get_customer_account_by_id",
        "get_customer_position_by_customer_id",
        "get_customer_position_by_id",
        "get_account_position_by_account_id",
        "get_account_position_by_id",
        "get_transaction_by_customer_id",
        "get_transaction_by_transaction_id",
    }
    assert expected.issubset(names)


@pytest.mark.asyncio
async def test_custody_tool_annotations() -> None:
    tools = {t.name: t for t in await mcp.list_tools()}
    get_customers = tools["get_customers"]
    assert get_customers.annotations is not None
    assert get_customers.annotations.readOnlyHint is True
    assert get_customers.annotations.idempotentHint is True
    assert get_customers.annotations.openWorldHint is True


@pytest.mark.asyncio
async def test_get_customers_tool_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": "C9", "number": "9"}])

    client = OpenWealthHttpClient(
        settings=_settings(), base_url=_CUSTODY_URL, transport=httpx.MockTransport(handler)
    )
    set_client(client)
    try:
        result = await mcp.call_tool("get_customers", {"limit": 1})
        # FastMCP may return CallToolResult or content list depending on version
        text = _tool_text(result)
        payload = json.loads(text)
        assert payload["data"][0]["id"] == "C9"
    finally:
        set_client(None)
        await client.aclose()


def _tool_text(result: object) -> str:
    if isinstance(result, str):
        return result
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict) and "result" in structured:
        value = structured["result"]
        return value if isinstance(value, str) else json.dumps(value, default=str)
    if hasattr(result, "content"):
        content = result.content  # type: ignore[attr-defined]
        if content and hasattr(content[0], "text"):
            return content[0].text
    if isinstance(result, tuple) and result:
        first = result[0]
        if isinstance(first, list) and first and hasattr(first[0], "text"):
            return first[0].text
    raise AssertionError(f"Unexpected tool result shape: {type(result)!r} {result!r}")
