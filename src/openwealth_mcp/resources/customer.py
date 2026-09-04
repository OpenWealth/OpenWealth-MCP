"""MCP resource providers for OpenWealth Customer Management API v2.0.6."""

from __future__ import annotations

import yaml
from fastmcp import FastMCP

from openwealth_mcp.resources._spec_path import resolve_spec_path

_SPEC_SUMMARY = """\
# OpenWealth Customer Management API v2.0.6

Docs: https://sandbox.openwealth.synpulse8.com/docs?api=customer-management-2-0-6

## IMPORTANT: Write operations

`create_customer`, `create_person`, `create_contact`, `create_address`,
`create_document`, `create_kyc` and `create_prospect_precheck` mutate live
customer data at the custody bank.  Always confirm details with the user
before calling write tools.  None of these POSTs are retried to avoid
duplicate records.

## Tool reference

| Tool | operationId | Method path |
|------|-------------|-------------|
| get_customers | getCustomers | GET /customers |
| create_customer | postCustomer | POST /customer-details |
| get_customer | getCustomerByCustomerId | GET /customers/{customerId} |
| get_customer_details | getCustomerDetailsByCustomerId | GET /customers/{customerId}/customer-details |
| get_persons | getPersons | GET /customers/{customerId}/persons |
| create_person | postPerson | POST /customers/{customerId}/person-details |
| get_person | getPersonByPersonId | GET /customers/{customerId}/persons/{personId} |
| get_person_details | getPersonDetailsByPersonId | GET /customers/{customerId}/person-details/{personId} |
| get_contacts | getContactDetailsByCustomerId | GET /customers/{customerId}/persons/{personId}/contacts |
| create_contact | postContactDetailsByCustomerId | POST /customers/{customerId}/persons/{personId}/contacts |
| get_contact | getContactDetailsByContactDetailID | GET /customers/{customerId}/persons/{personId}/contacts/{contactId} |
| update_contact | putContactDetailByContactDetailId | PUT /customers/{customerId}/persons/{personId}/contacts/{contactId} |
| delete_contact | deleteContactDetailsByContactDetailID | DELETE /customers/{customerId}/persons/{personId}/contacts/{contactId} |
| get_addresses | getAddressByCustomerId | GET /customers/{customerId}/persons/{personId}/addresses |
| create_address | postAddressByCustomerId | POST /customers/{customerId}/persons/{personId}/addresses |
| get_address | getAddressByAddressId | GET /customers/{customerId}/persons/{personId}/addresses/{addressId} |
| update_address | putAddressByCustomerId | PUT /customers/{customerId}/persons/{personId}/addresses/{addressId} |
| get_documents | getDocumentsByCustomerId | GET /customers/{customerId}/documents |
| create_document | postDocumentByCustomerId | POST /customers/{customerId}/document-details |
| get_document | getDocumentByDocumentId | GET /customers/{customerId}/documents/{documentId} |
| get_document_details | getDocumentDetailsByDocumentId | GET /customers/{customerId}/documents/{documentId}/document-details |
| get_kyc | getKycByCustomerId | GET /customers/{customerId}/persons/{personId}/kyc |
| create_kyc | postKyc | POST /customers/{customerId}/persons/{personId}/kyc |
| create_prospect_precheck | postProspect | POST /prospect-precheck |
| get_prospect_precheck | getPreCheck | GET /prospect-precheck/{temporaryId} |
| get_status | getStatusByTemporaryId | GET /status/{temporaryId} |
"""

_SPEC_NOT_FOUND = "customerAPI.yaml not found; ensure specs/customerAPI.yaml is present."


def register_customer_resources(mcp: FastMCP) -> None:
    """Register Customer Management spec resources on the MCP server."""

    @mcp.resource("openwealth://specs/customer")
    def customer_spec_summary() -> str:
        """Summary of Customer Management API v2.0.6 endpoints exposed as tools."""
        return _SPEC_SUMMARY

    @mcp.resource("openwealth://specs/customer.yaml")
    def customer_spec_yaml() -> str:
        """Schema reference for Customer Management API v2.0.6.

        Use this resource to understand request/response schemas and field types.
        All API interactions MUST go through the provided MCP tools — never
        construct or call HTTP endpoints directly.
        """
        path = resolve_spec_path("customerAPI.yaml")
        if path is None:
            return _SPEC_NOT_FOUND
        spec: dict[str, object] = yaml.safe_load(path.read_text(encoding="utf-8"))
        spec.pop("servers", None)
        spec.pop("security", None)
        components = spec.get("components")
        if isinstance(components, dict):
            components.pop("securitySchemes", None)
        return yaml.dump(spec, allow_unicode=True, sort_keys=False)
