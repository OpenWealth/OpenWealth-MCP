"""Customer Management domain service — one method per OpenAPI operationId.

This layer owns all path construction and query-parameter assembly so that
the MCP tool adapters remain thin (one-liners).  It has no MCP or HTTP-
transport knowledge; it delegates every network call to ``OpenWealthHttpClient``.

API: OpenWealth Customer Management API v2.0.6
Spec: https://github.com/swissfintechinnovations/ca-wealth/blob/main/CustomerManagement.yaml
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from openwealth_mcp.client import OpenWealthHttpClient
from openwealth_mcp.validation import validate_id, validate_limit


def _seg(value: str) -> str:
    return quote(value, safe="")


class CustomerService:
    """Maps OpenWealth Customer Management operationIds to HTTP calls."""

    def __init__(self, client: OpenWealthHttpClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    async def get_customers(
        self,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """operationId: getCustomers — GET /customers."""
        return await self._client.get(
            "/customers",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )

    async def create_customer(self, customer_details: dict[str, Any]) -> str:
        """operationId: postCustomer — POST /customer-details.

        Opens a new customer relationship at the custody bank.
        NOT retried: duplicate customer creation is a data error.
        """
        return await self._client.post("/customer-details", body=customer_details, idempotent=False)

    async def get_customer(self, customer_id: str) -> str:
        """operationId: getCustomerByCustomerId — GET /customers/{customerId}."""
        cid = validate_id(customer_id, "customer_id")
        return await self._client.get(f"/customers/{_seg(cid)}")

    async def get_customer_details(self, customer_id: str) -> str:
        """operationId: getCustomerDetailsByCustomerId — GET /customers/{customerId}/customer-details."""
        cid = validate_id(customer_id, "customer_id")
        return await self._client.get(f"/customers/{_seg(cid)}/customer-details")

    # ------------------------------------------------------------------
    # Persons
    # ------------------------------------------------------------------

    async def get_persons(
        self,
        customer_id: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """operationId: getPersons — GET /customers/{customerId}/persons."""
        cid = validate_id(customer_id, "customer_id")
        return await self._client.get(
            f"/customers/{_seg(cid)}/persons",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )

    async def create_person(self, customer_id: str, person_details: dict[str, Any]) -> str:
        """operationId: postPerson — POST /customers/{customerId}/person-details.

        NOT retried: duplicate person creation is a data error.
        """
        cid = validate_id(customer_id, "customer_id")
        return await self._client.post(
            f"/customers/{_seg(cid)}/person-details", body=person_details, idempotent=False
        )

    async def get_person(self, customer_id: str, person_id: str) -> str:
        """operationId: getPersonByPersonId — GET /customers/{customerId}/persons/{personId}."""
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        return await self._client.get(f"/customers/{_seg(cid)}/persons/{_seg(pid)}")

    async def get_person_details(self, customer_id: str, person_id: str) -> str:
        """operationId: getPersonDetailsByPersonId — GET /customers/{customerId}/person-details/{personId}."""
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        return await self._client.get(f"/customers/{_seg(cid)}/person-details/{_seg(pid)}")

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    async def get_contacts(
        self,
        customer_id: str,
        person_id: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """operationId: getContactDetailsByCustomerId — GET /customers/{customerId}/persons/{personId}/contacts."""
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        return await self._client.get(
            f"/customers/{_seg(cid)}/persons/{_seg(pid)}/contacts",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )

    async def create_contact(
        self, customer_id: str, person_id: str, contact: dict[str, Any]
    ) -> str:
        """operationId: postContactDetailsByCustomerId — POST /customers/{customerId}/persons/{personId}/contacts.

        NOT retried: duplicate contact creation is a data error.
        """
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        return await self._client.post(
            f"/customers/{_seg(cid)}/persons/{_seg(pid)}/contacts",
            body=contact,
            idempotent=False,
        )

    async def get_contact(self, customer_id: str, person_id: str, contact_id: str) -> str:
        """operationId: getContactDetailsByContactDetailID — GET /customers/{customerId}/persons/{personId}/contacts/{contactId}."""
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        coid = validate_id(contact_id, "contact_id")
        return await self._client.get(
            f"/customers/{_seg(cid)}/persons/{_seg(pid)}/contacts/{_seg(coid)}"
        )

    async def update_contact(
        self, customer_id: str, person_id: str, contact_id: str, contact: dict[str, Any]
    ) -> str:
        """operationId: putContactDetailByContactDetailId — PUT /customers/{customerId}/persons/{personId}/contacts/{contactId}."""
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        coid = validate_id(contact_id, "contact_id")
        return await self._client.put(
            f"/customers/{_seg(cid)}/persons/{_seg(pid)}/contacts/{_seg(coid)}",
            body=contact,
        )

    async def delete_contact(self, customer_id: str, person_id: str, contact_id: str) -> str:
        """operationId: deleteContactDetailsByContactDetailID — DELETE /customers/{customerId}/persons/{personId}/contacts/{contactId}."""
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        coid = validate_id(contact_id, "contact_id")
        return await self._client.delete(
            f"/customers/{_seg(cid)}/persons/{_seg(pid)}/contacts/{_seg(coid)}"
        )

    # ------------------------------------------------------------------
    # Addresses
    # ------------------------------------------------------------------

    async def get_addresses(
        self,
        customer_id: str,
        person_id: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """operationId: getAddressByCustomerId — GET /customers/{customerId}/persons/{personId}/addresses."""
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        return await self._client.get(
            f"/customers/{_seg(cid)}/persons/{_seg(pid)}/addresses",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )

    async def create_address(
        self, customer_id: str, person_id: str, address: dict[str, Any]
    ) -> str:
        """operationId: postAddressByCustomerId — POST /customers/{customerId}/persons/{personId}/addresses.

        NOT retried: duplicate address creation is a data error.
        """
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        return await self._client.post(
            f"/customers/{_seg(cid)}/persons/{_seg(pid)}/addresses",
            body=address,
            idempotent=False,
        )

    async def get_address(self, customer_id: str, person_id: str, address_id: str) -> str:
        """operationId: getAddressByAddressId — GET /customers/{customerId}/persons/{personId}/addresses/{addressId}."""
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        aid = validate_id(address_id, "address_id")
        return await self._client.get(
            f"/customers/{_seg(cid)}/persons/{_seg(pid)}/addresses/{_seg(aid)}"
        )

    async def update_address(
        self, customer_id: str, person_id: str, address_id: str, address: dict[str, Any]
    ) -> str:
        """operationId: putAddressByCustomerId — PUT /customers/{customerId}/persons/{personId}/addresses/{addressId}."""
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        aid = validate_id(address_id, "address_id")
        return await self._client.put(
            f"/customers/{_seg(cid)}/persons/{_seg(pid)}/addresses/{_seg(aid)}",
            body=address,
        )

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    async def get_documents(
        self,
        customer_id: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """operationId: getDocumentsByCustomerId — GET /customers/{customerId}/documents."""
        cid = validate_id(customer_id, "customer_id")
        return await self._client.get(
            f"/customers/{_seg(cid)}/documents",
            params={"cursor": cursor, "limit": validate_limit(limit)},
        )

    async def create_document(self, customer_id: str, document_details: dict[str, Any]) -> str:
        """operationId: postDocumentByCustomerId — POST /customers/{customerId}/document-details.

        NOT retried: duplicate document creation is a data error.
        """
        cid = validate_id(customer_id, "customer_id")
        return await self._client.post(
            f"/customers/{_seg(cid)}/document-details", body=document_details, idempotent=False
        )

    async def get_document(self, customer_id: str, document_id: str) -> str:
        """operationId: getDocumentByDocumentId — GET /customers/{customerId}/documents/{documentId}."""
        cid = validate_id(customer_id, "customer_id")
        did = validate_id(document_id, "document_id")
        return await self._client.get(f"/customers/{_seg(cid)}/documents/{_seg(did)}")

    async def get_document_details(self, customer_id: str, document_id: str) -> str:
        """operationId: getDocumentDetailsByDocumentId — GET /customers/{customerId}/documents/{documentId}/document-details."""
        cid = validate_id(customer_id, "customer_id")
        did = validate_id(document_id, "document_id")
        return await self._client.get(
            f"/customers/{_seg(cid)}/documents/{_seg(did)}/document-details"
        )

    # ------------------------------------------------------------------
    # KYC
    # ------------------------------------------------------------------

    async def get_kyc(self, customer_id: str, person_id: str) -> str:
        """operationId: getKycByCustomerId — GET /customers/{customerId}/persons/{personId}/kyc."""
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        return await self._client.get(f"/customers/{_seg(cid)}/persons/{_seg(pid)}/kyc")

    async def create_kyc(self, customer_id: str, person_id: str, kyc: dict[str, Any]) -> str:
        """operationId: postKyc — POST /customers/{customerId}/persons/{personId}/kyc.

        NOT retried: duplicate KYC submission is a compliance data error.
        """
        cid = validate_id(customer_id, "customer_id")
        pid = validate_id(person_id, "person_id")
        return await self._client.post(
            f"/customers/{_seg(cid)}/persons/{_seg(pid)}/kyc",
            body=kyc,
            idempotent=False,
        )

    # ------------------------------------------------------------------
    # Prospect pre-check
    # ------------------------------------------------------------------

    async def create_prospect_precheck(self, prospect: dict[str, Any]) -> str:
        """operationId: postProspect — POST /prospect-precheck.

        Conducts a pre-check at the custody bank before onboarding.
        NOT retried: duplicate pre-check submissions may create ghost prospects.
        """
        return await self._client.post("/prospect-precheck", body=prospect, idempotent=False)

    async def get_prospect_precheck(self, temporary_id: str) -> str:
        """operationId: getPreCheck — GET /prospect-precheck/{temporaryId}."""
        tid = validate_id(temporary_id, "temporary_id")
        return await self._client.get(f"/prospect-precheck/{_seg(tid)}")

    async def get_status(self, temporary_id: str) -> str:
        """operationId: getStatusByTemporaryId — GET /status/{temporaryId}."""
        tid = validate_id(temporary_id, "temporary_id")
        return await self._client.get(f"/status/{_seg(tid)}")
