"""MCP tool adapters for OpenWealth Customer Management API v2.0.6.

Each adapter is a thin shim: it carries the ``Annotated`` schema that the LLM
sees and delegates the actual work to ``CustomerService``.  Error handling and
logging live in ``invoke_tool``; the adapters themselves have no try/except.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable
from typing import Annotated, Any

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from openwealth_mcp.customer.app import get_customer_app, set_customer_client
from openwealth_mcp.errors import (
    OpenWealthApiError,
    OpenWealthError,
    TransportError,
)
from openwealth_mcp.logging_config import get_logger

_log = get_logger("openwealth_mcp.tools.customer")

__all__ = ["register_customer_tools", "set_customer_client"]

_READ = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True)
_WRITE_ADDITIVE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True
)
_WRITE_IDEMPOTENT = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True
)
_WRITE_DESTRUCTIVE_IDEMPOTENT = ToolAnnotations(
    readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=True
)


# ---------------------------------------------------------------------------
# Tool gateway — unified logging + error mapping (mirrors custody/trading pattern)
# ---------------------------------------------------------------------------


async def invoke_tool(operation: str, awaitable: Awaitable[str]) -> str:
    """Execute a service call and map errors to safe JSON tool results."""
    _log.info("tool start operation=%s", operation)
    try:
        result = await awaitable
        _log.info("tool ok operation=%s", operation)
        return result
    except OpenWealthApiError as exc:
        _log.warning(
            "tool api error operation=%s status=%s code=%s message=%s",
            operation,
            exc.status_code,
            exc.error_code,
            exc.message,
        )
        return exc.to_tool_result()
    except TransportError as exc:
        _log.warning("tool transport error operation=%s message=%s", operation, exc.message)
        return exc.to_tool_result()
    except OpenWealthError as exc:
        _log.warning("tool error operation=%s code=%s message=%s", operation, exc.error_code, exc)
        return exc.to_tool_result()
    except Exception as exc:  # noqa: BLE001
        _log.exception("tool unexpected error operation=%s", operation)
        return json.dumps(
            {
                "error": True,
                "error_code": "INTERNAL_ERROR",
                "message": f"{type(exc).__name__}: unexpected failure",
                "retryable": False,
            },
            default=str,
        )


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register_customer_tools(mcp: FastMCP) -> None:
    """Register all 26 Customer Management tools on the given FastMCP server."""

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    @mcp.tool(
        name="get_customers",
        description=(
            "OpenWealth Customer Management operationId=getCustomers. "
            "Returns a paginated list of customers (natural persons). "
            "Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def get_customers(
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "getCustomers",
            get_customer_app().service.get_customers(cursor=cursor, limit=limit),
        )

    @mcp.tool(
        name="create_customer",
        description=(
            "OpenWealth Customer Management operationId=postCustomer. "
            "Opens a new customer relationship at the custody bank. "
            "IMPORTANT: mutates live customer data — confirm all details before calling. "
            "Not retried to avoid duplicate customer records."
        ),
        annotations=_WRITE_ADDITIVE,
    )
    async def create_customer(
        customer_details: Annotated[
            dict[str, Any],
            "customerDetails object per the Customer Management OpenAPI schema.",
        ],
    ) -> str:
        return await invoke_tool(
            "postCustomer",
            get_customer_app().service.create_customer(customer_details),
        )

    @mcp.tool(
        name="get_customer",
        description=(
            "OpenWealth Customer Management operationId=getCustomerByCustomerId. "
            "Returns the summary record of a specific customer."
        ),
        annotations=_READ,
    )
    async def get_customer(
        customer_id: Annotated[str, "Customer identifier (UUID or bank-assigned ID)"],
    ) -> str:
        return await invoke_tool(
            "getCustomerByCustomerId",
            get_customer_app().service.get_customer(customer_id),
        )

    @mcp.tool(
        name="get_customer_details",
        description=(
            "OpenWealth Customer Management operationId=getCustomerDetailsByCustomerId. "
            "Returns the full record of a specific customer including all sub-objects."
        ),
        annotations=_READ,
    )
    async def get_customer_details(
        customer_id: Annotated[str, "Customer identifier"],
    ) -> str:
        return await invoke_tool(
            "getCustomerDetailsByCustomerId",
            get_customer_app().service.get_customer_details(customer_id),
        )

    # ------------------------------------------------------------------
    # Persons
    # ------------------------------------------------------------------

    @mcp.tool(
        name="get_persons",
        description=(
            "OpenWealth Customer Management operationId=getPersons. "
            "Returns a paginated list of persons associated with a specific customer. "
            "Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def get_persons(
        customer_id: Annotated[str, "Customer identifier"],
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "getPersons",
            get_customer_app().service.get_persons(customer_id, cursor=cursor, limit=limit),
        )

    @mcp.tool(
        name="create_person",
        description=(
            "OpenWealth Customer Management operationId=postPerson. "
            "Creates a new person object associated with a specific customer. "
            "IMPORTANT: mutates live customer data — confirm details before calling. "
            "Not retried to avoid duplicate person records."
        ),
        annotations=_WRITE_ADDITIVE,
    )
    async def create_person(
        customer_id: Annotated[str, "Customer identifier"],
        person_details: Annotated[
            dict[str, Any],
            "personDetails object per the Customer Management OpenAPI schema.",
        ],
    ) -> str:
        return await invoke_tool(
            "postPerson",
            get_customer_app().service.create_person(customer_id, person_details),
        )

    @mcp.tool(
        name="get_person",
        description=(
            "OpenWealth Customer Management operationId=getPersonByPersonId. "
            "Returns the summary record of a specific person."
        ),
        annotations=_READ,
    )
    async def get_person(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
    ) -> str:
        return await invoke_tool(
            "getPersonByPersonId",
            get_customer_app().service.get_person(customer_id, person_id),
        )

    @mcp.tool(
        name="get_person_details",
        description=(
            "OpenWealth Customer Management operationId=getPersonDetailsByPersonId. "
            "Returns the full record of a specific person including all sub-objects."
        ),
        annotations=_READ,
    )
    async def get_person_details(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
    ) -> str:
        return await invoke_tool(
            "getPersonDetailsByPersonId",
            get_customer_app().service.get_person_details(customer_id, person_id),
        )

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    @mcp.tool(
        name="get_contacts",
        description=(
            "OpenWealth Customer Management operationId=getContactDetailsByCustomerId. "
            "Returns a paginated list of contact details (phone, email, etc.) "
            "for a specific person. Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def get_contacts(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "getContactDetailsByCustomerId",
            get_customer_app().service.get_contacts(
                customer_id, person_id, cursor=cursor, limit=limit
            ),
        )

    @mcp.tool(
        name="create_contact",
        description=(
            "OpenWealth Customer Management operationId=postContactDetailsByCustomerId. "
            "Creates a new contact detail for a specific person. "
            "Not retried to avoid duplicate contact records."
        ),
        annotations=_WRITE_ADDITIVE,
    )
    async def create_contact(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
        contact: Annotated[
            dict[str, Any],
            "contact object per the Customer Management OpenAPI schema.",
        ],
    ) -> str:
        return await invoke_tool(
            "postContactDetailsByCustomerId",
            get_customer_app().service.create_contact(customer_id, person_id, contact),
        )

    @mcp.tool(
        name="get_contact",
        description=(
            "OpenWealth Customer Management operationId=getContactDetailsByContactDetailID. "
            "Returns a specific contact detail by ID."
        ),
        annotations=_READ,
    )
    async def get_contact(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
        contact_id: Annotated[str, "Contact detail identifier"],
    ) -> str:
        return await invoke_tool(
            "getContactDetailsByContactDetailID",
            get_customer_app().service.get_contact(customer_id, person_id, contact_id),
        )

    @mcp.tool(
        name="update_contact",
        description=(
            "OpenWealth Customer Management operationId=putContactDetailByContactDetailId. "
            "Updates specific field(s) of a specific contact detail (idempotent PUT)."
        ),
        annotations=_WRITE_IDEMPOTENT,
    )
    async def update_contact(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
        contact_id: Annotated[str, "Contact detail identifier"],
        contact: Annotated[
            dict[str, Any],
            "Updated contact object per the Customer Management OpenAPI schema.",
        ],
    ) -> str:
        return await invoke_tool(
            "putContactDetailByContactDetailId",
            get_customer_app().service.update_contact(customer_id, person_id, contact_id, contact),
        )

    @mcp.tool(
        name="delete_contact",
        description=(
            "OpenWealth Customer Management operationId=deleteContactDetailsByContactDetailID. "
            "Deletes a specific contact detail (idempotent DELETE)."
        ),
        annotations=_WRITE_DESTRUCTIVE_IDEMPOTENT,
    )
    async def delete_contact(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
        contact_id: Annotated[str, "Contact detail identifier"],
    ) -> str:
        return await invoke_tool(
            "deleteContactDetailsByContactDetailID",
            get_customer_app().service.delete_contact(customer_id, person_id, contact_id),
        )

    # ------------------------------------------------------------------
    # Addresses
    # ------------------------------------------------------------------

    @mcp.tool(
        name="get_addresses",
        description=(
            "OpenWealth Customer Management operationId=getAddressByCustomerId. "
            "Returns a paginated list of addresses for a specific person. "
            "Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def get_addresses(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "getAddressByCustomerId",
            get_customer_app().service.get_addresses(
                customer_id, person_id, cursor=cursor, limit=limit
            ),
        )

    @mcp.tool(
        name="create_address",
        description=(
            "OpenWealth Customer Management operationId=postAddressByCustomerId. "
            "Creates a new address for a specific person. "
            "Not retried to avoid duplicate address records."
        ),
        annotations=_WRITE_ADDITIVE,
    )
    async def create_address(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
        address: Annotated[
            dict[str, Any],
            "address object per the Customer Management OpenAPI schema.",
        ],
    ) -> str:
        return await invoke_tool(
            "postAddressByCustomerId",
            get_customer_app().service.create_address(customer_id, person_id, address),
        )

    @mcp.tool(
        name="get_address",
        description=(
            "OpenWealth Customer Management operationId=getAddressByAddressId. "
            "Returns a specific address by ID."
        ),
        annotations=_READ,
    )
    async def get_address(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
        address_id: Annotated[str, "Address identifier"],
    ) -> str:
        return await invoke_tool(
            "getAddressByAddressId",
            get_customer_app().service.get_address(customer_id, person_id, address_id),
        )

    @mcp.tool(
        name="update_address",
        description=(
            "OpenWealth Customer Management operationId=putAddressByCustomerId. "
            "Updates an existing address (idempotent PUT)."
        ),
        annotations=_WRITE_IDEMPOTENT,
    )
    async def update_address(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
        address_id: Annotated[str, "Address identifier"],
        address: Annotated[
            dict[str, Any],
            "Updated address object per the Customer Management OpenAPI schema.",
        ],
    ) -> str:
        return await invoke_tool(
            "putAddressByCustomerId",
            get_customer_app().service.update_address(customer_id, person_id, address_id, address),
        )

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    @mcp.tool(
        name="get_documents",
        description=(
            "OpenWealth Customer Management operationId=getDocumentsByCustomerId. "
            "Returns a paginated list of documents for a specific customer "
            "(without actual document content). Supports cursor pagination."
        ),
        annotations=_READ,
    )
    async def get_documents(
        customer_id: Annotated[str, "Customer identifier"],
        cursor: Annotated[str | None, "Opaque pagination cursor"] = None,
        limit: Annotated[int | None, "Maximum number of items to return"] = None,
    ) -> str:
        return await invoke_tool(
            "getDocumentsByCustomerId",
            get_customer_app().service.get_documents(customer_id, cursor=cursor, limit=limit),
        )

    @mcp.tool(
        name="create_document",
        description=(
            "OpenWealth Customer Management operationId=postDocumentByCustomerId. "
            "Creates a new document for a specific customer. "
            "IMPORTANT: mutates live customer data — confirm details before calling. "
            "Not retried to avoid duplicate document records."
        ),
        annotations=_WRITE_ADDITIVE,
    )
    async def create_document(
        customer_id: Annotated[str, "Customer identifier"],
        document_details: Annotated[
            dict[str, Any],
            "documentDetails object per the Customer Management OpenAPI schema.",
        ],
    ) -> str:
        return await invoke_tool(
            "postDocumentByCustomerId",
            get_customer_app().service.create_document(customer_id, document_details),
        )

    @mcp.tool(
        name="get_document",
        description=(
            "OpenWealth Customer Management operationId=getDocumentByDocumentId. "
            "Returns a specific document record (without content) by ID."
        ),
        annotations=_READ,
    )
    async def get_document(
        customer_id: Annotated[str, "Customer identifier"],
        document_id: Annotated[str, "Document identifier"],
    ) -> str:
        return await invoke_tool(
            "getDocumentByDocumentId",
            get_customer_app().service.get_document(customer_id, document_id),
        )

    @mcp.tool(
        name="get_document_details",
        description=(
            "OpenWealth Customer Management operationId=getDocumentDetailsByDocumentId. "
            "Returns the full record of a specific document including details."
        ),
        annotations=_READ,
    )
    async def get_document_details(
        customer_id: Annotated[str, "Customer identifier"],
        document_id: Annotated[str, "Document identifier"],
    ) -> str:
        return await invoke_tool(
            "getDocumentDetailsByDocumentId",
            get_customer_app().service.get_document_details(customer_id, document_id),
        )

    # ------------------------------------------------------------------
    # KYC
    # ------------------------------------------------------------------

    @mcp.tool(
        name="get_kyc",
        description=(
            "OpenWealth Customer Management operationId=getKycByCustomerId. "
            "Returns the KYC record of a specific person associated with a customer."
        ),
        annotations=_READ,
    )
    async def get_kyc(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
    ) -> str:
        return await invoke_tool(
            "getKycByCustomerId",
            get_customer_app().service.get_kyc(customer_id, person_id),
        )

    @mcp.tool(
        name="create_kyc",
        description=(
            "OpenWealth Customer Management operationId=postKyc. "
            "Creates a new KYC record for a specific person. "
            "IMPORTANT: mutates live KYC data at the custody bank — confirm all details. "
            "Not retried to avoid duplicate KYC submissions."
        ),
        annotations=_WRITE_ADDITIVE,
    )
    async def create_kyc(
        customer_id: Annotated[str, "Customer identifier"],
        person_id: Annotated[str, "Person identifier"],
        kyc: Annotated[
            dict[str, Any],
            "kyc object per the Customer Management OpenAPI schema.",
        ],
    ) -> str:
        return await invoke_tool(
            "postKyc",
            get_customer_app().service.create_kyc(customer_id, person_id, kyc),
        )

    # ------------------------------------------------------------------
    # Prospect pre-check and status
    # ------------------------------------------------------------------

    @mcp.tool(
        name="create_prospect_precheck",
        description=(
            "OpenWealth Customer Management operationId=postProspect. "
            "Conducts a pre-check at the custody bank before onboarding a new customer. "
            "Returns a temporaryId to query the result. "
            "Not retried to avoid duplicate pre-check submissions."
        ),
        annotations=_WRITE_ADDITIVE,
    )
    async def create_prospect_precheck(
        prospect: Annotated[
            dict[str, Any],
            "prospect object per the Customer Management OpenAPI schema.",
        ],
    ) -> str:
        return await invoke_tool(
            "postProspect",
            get_customer_app().service.create_prospect_precheck(prospect),
        )

    @mcp.tool(
        name="get_prospect_precheck",
        description=(
            "OpenWealth Customer Management operationId=getPreCheck. "
            "Returns the result of a prospect pre-check by temporaryId."
        ),
        annotations=_READ,
    )
    async def get_prospect_precheck(
        temporary_id: Annotated[str, "Temporary identifier returned by create_prospect_precheck"],
    ) -> str:
        return await invoke_tool(
            "getPreCheck",
            get_customer_app().service.get_prospect_precheck(temporary_id),
        )

    @mcp.tool(
        name="get_status",
        description=(
            "OpenWealth Customer Management operationId=getStatusByTemporaryId. "
            "Returns the processing status of a customer management request by temporaryId."
        ),
        annotations=_READ,
    )
    async def get_status(
        temporary_id: Annotated[
            str, "Temporary identifier returned by an async customer management request"
        ],
    ) -> str:
        return await invoke_tool(
            "getStatusByTemporaryId",
            get_customer_app().service.get_status(temporary_id),
        )
