"""Unit tests for CustomerService — validates path building and param assembly."""

import json

import httpx
import pytest

from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.config import Settings
from openwealth_mcp.customer.service import CustomerService

_CUSTOMER_URL = "https://api.example.com/api/customer-management/v2"


def _settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        customer_management_base_url=_CUSTOMER_URL,
        bearer_token="svc-token",
        correlation_id="svc-cid",
        max_retries=0,
        _env_file=None,
    )


def _make_service(handler) -> tuple[CustomerService, OpenWealthHttpClient]:  # type: ignore[type-arg]
    client = OpenWealthHttpClient(
        settings=_settings(),
        base_url=_CUSTOMER_URL,
        transport=httpx.MockTransport(handler),
    )
    return CustomerService(client), client


# ---------------------------------------------------------------------------
# Customer endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_customers_path_and_params() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers")
        assert request.url.params.get("limit") == "10"
        return httpx.Response(200, json=[{"id": "C1"}])

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_customers(limit=10)
    assert json.loads(raw)["data"][0]["id"] == "C1"


@pytest.mark.asyncio
async def test_get_customer_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C42")
        return httpx.Response(200, json={"id": "C42"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_customer("C42")
    assert json.loads(raw)["data"]["id"] == "C42"


@pytest.mark.asyncio
async def test_get_customer_details_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C42/customer-details")
        return httpx.Response(200, json={"id": "C42"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_customer_details("C42")
    assert json.loads(raw)["data"]["id"] == "C42"


@pytest.mark.asyncio
async def test_create_customer_posts_body() -> None:
    body_received: dict = {}  # type: ignore[type-arg]

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal body_received
        assert request.url.path.endswith("/customer-details")
        assert request.method == "POST"
        body_received = json.loads(request.content)
        return httpx.Response(202, json={"temporaryId": "T1"})

    service, client = _make_service(handler)
    async with client:
        await service.create_customer({"firstName": "Alice"})
    assert body_received["firstName"] == "Alice"


# ---------------------------------------------------------------------------
# Person endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_persons_path_and_params() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/customers/C1/persons" in request.url.path
        assert request.url.params.get("limit") == "5"
        return httpx.Response(200, json=[{"personId": "P1"}])

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_persons("C1", limit=5)
    assert json.loads(raw)["data"][0]["personId"] == "P1"


@pytest.mark.asyncio
async def test_get_person_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/persons/P2")
        return httpx.Response(200, json={"personId": "P2"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_person("C1", "P2")
    assert json.loads(raw)["data"]["personId"] == "P2"


@pytest.mark.asyncio
async def test_get_person_details_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/person-details/P2")
        return httpx.Response(200, json={"personId": "P2"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_person_details("C1", "P2")
    assert json.loads(raw)["data"]["personId"] == "P2"


# ---------------------------------------------------------------------------
# Contact endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_contacts_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/customers/C1/persons/P1/contacts" in request.url.path
        return httpx.Response(200, json=[{"contactId": "CO1"}])

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_contacts("C1", "P1")
    assert json.loads(raw)["data"][0]["contactId"] == "CO1"


@pytest.mark.asyncio
async def test_get_contact_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/persons/P1/contacts/CO2")
        return httpx.Response(200, json={"contactId": "CO2"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_contact("C1", "P1", "CO2")
    assert json.loads(raw)["data"]["contactId"] == "CO2"


@pytest.mark.asyncio
async def test_delete_contact_method_and_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path.endswith("/customers/C1/persons/P1/contacts/CO3")
        return httpx.Response(204, text="")

    service, client = _make_service(handler)
    async with client:
        await service.delete_contact("C1", "P1", "CO3")


@pytest.mark.asyncio
async def test_update_contact_method_and_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert request.url.path.endswith("/customers/C1/persons/P1/contacts/CO4")
        return httpx.Response(200, json={"contactId": "CO4"})

    service, client = _make_service(handler)
    async with client:
        await service.update_contact("C1", "P1", "CO4", {"type": "email"})


# ---------------------------------------------------------------------------
# Address endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_addresses_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/customers/C1/persons/P1/addresses" in request.url.path
        return httpx.Response(200, json=[{"addressId": "A1"}])

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_addresses("C1", "P1")
    assert json.loads(raw)["data"][0]["addressId"] == "A1"


@pytest.mark.asyncio
async def test_get_address_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/persons/P1/addresses/A2")
        return httpx.Response(200, json={"addressId": "A2"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_address("C1", "P1", "A2")
    assert json.loads(raw)["data"]["addressId"] == "A2"


# ---------------------------------------------------------------------------
# Document endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_documents_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/customers/C1/documents" in request.url.path
        return httpx.Response(200, json=[{"documentId": "D1"}])

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_documents("C1")
    assert json.loads(raw)["data"][0]["documentId"] == "D1"


@pytest.mark.asyncio
async def test_get_document_details_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/documents/D2/document-details")
        return httpx.Response(200, json={"documentId": "D2"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_document_details("C1", "D2")
    assert json.loads(raw)["data"]["documentId"] == "D2"


# ---------------------------------------------------------------------------
# KYC
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_kyc_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/persons/P1/kyc")
        return httpx.Response(200, json={"kycId": "K1"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_kyc("C1", "P1")
    assert json.loads(raw)["data"]["kycId"] == "K1"


@pytest.mark.asyncio
async def test_create_kyc_posts_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/customers/C1/persons/P1/kyc")
        return httpx.Response(202, json={"temporaryId": "T2"})

    service, client = _make_service(handler)
    async with client:
        await service.create_kyc("C1", "P1", {"totalWealth": {"amount": 100000}})


# ---------------------------------------------------------------------------
# Prospect pre-check and status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_prospect_precheck_posts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/prospect-precheck")
        return httpx.Response(202, json={"temporaryId": "T3"})

    service, client = _make_service(handler)
    async with client:
        await service.create_prospect_precheck({"firstName": "Bob"})


@pytest.mark.asyncio
async def test_get_prospect_precheck_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/prospect-precheck/TMP1")
        return httpx.Response(200, json={"status": "ok"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_prospect_precheck("TMP1")
    assert json.loads(raw)["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_get_status_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/status/TMP2")
        return httpx.Response(200, json={"status": "completed"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_status("TMP2")
    assert json.loads(raw)["data"]["status"] == "completed"


# ---------------------------------------------------------------------------
# Path encoding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_path_encodes_special_characters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "customers/a%2Fb" in str(request.url)
        return httpx.Response(200, json={"id": "a/b"})

    service, client = _make_service(handler)
    async with client:
        await service.get_customer("a/b")


# ---------------------------------------------------------------------------
# Validation errors raised before HTTP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_person_posts_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/customers/C1/person-details")
        return httpx.Response(202, json={"temporaryId": "T1"})

    service, client = _make_service(handler)
    async with client:
        await service.create_person("C1", {"firstName": "Bob"})


@pytest.mark.asyncio
async def test_create_contact_posts_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert "/customers/C1/persons/P1/contacts" in request.url.path
        return httpx.Response(201, json={"contactId": "CO1"})

    service, client = _make_service(handler)
    async with client:
        await service.create_contact("C1", "P1", {"type": "email", "value": "a@b.com"})


@pytest.mark.asyncio
async def test_create_address_posts_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert "/customers/C1/persons/P1/addresses" in request.url.path
        return httpx.Response(201, json={"addressId": "A1"})

    service, client = _make_service(handler)
    async with client:
        await service.create_address("C1", "P1", {"street": "Main St"})


@pytest.mark.asyncio
async def test_update_address_puts_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert request.url.path.endswith("/customers/C1/persons/P1/addresses/A1")
        return httpx.Response(200, json={"addressId": "A1"})

    service, client = _make_service(handler)
    async with client:
        await service.update_address("C1", "P1", "A1", {"street": "New St"})


@pytest.mark.asyncio
async def test_create_document_posts_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/customers/C1/document-details")
        return httpx.Response(201, json={"documentId": "D1"})

    service, client = _make_service(handler)
    async with client:
        await service.create_document("C1", {"type": "passport"})


@pytest.mark.asyncio
async def test_get_document_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/C1/documents/D3")
        return httpx.Response(200, json={"documentId": "D3"})

    service, client = _make_service(handler)
    async with client:
        raw = await service.get_document("C1", "D3")
    assert json.loads(raw)["data"]["documentId"] == "D3"


@pytest.mark.asyncio
async def test_empty_customer_id_raises() -> None:
    from openwealth_mcp.errors import ToolValidationError

    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=[])

    service, client = _make_service(handler)
    async with client:
        with pytest.raises(ToolValidationError):
            await service.get_customer("")
    assert calls["n"] == 0
