# OpenWealth MCP

[![CI](https://github.com/OpenWealth/OpenWealth-MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/OpenWealth/OpenWealth-MCP/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/openwealth-mcp)](https://pypi.org/project/openwealth-mcp/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)

Three [FastMCP](https://gofastmcp.com/) servers that expose the
[OpenWealth](https://openwealth.ch/) APIs as MCP tools, so an AI assistant
(Claude, Cursor, any MCP client) can read custody data, manage orders, and
onboard customers through a typed, audited interface instead of raw HTTP.

| Server | API | Console script | Tools |
|--------|-----|----------------|-------|
| **Custody** | [Custody Services v3.2.0](https://sandbox.openwealth.synpulse8.com/docs?api=custody-services-3-2-0) — customers, accounts, positions, transactions | `openwealth-custody-mcp` | 10 (read-only) |
| **Trading** | [Order Placement v3.0.1](https://sandbox.openwealth.synpulse8.com/docs?api=order-placement-3-0-1) — orders, executions, quotes, subscriptions | `openwealth-trading-mcp` | 18 (full lifecycle) |
| **Customer** | [Customer Management v2.0.6](https://sandbox.openwealth.synpulse8.com/docs?api=customer-management-2-0-6) — customers, persons, contacts, addresses, documents, KYC | `openwealth-customer-mcp` | 26 (full lifecycle) |

All three ship in one Python package and speak **MCP over stdio**. OpenAPI specs are
vendored from [OpenWealth](https://openwealth.ch/)
and served as sanitized MCP resources (server URLs and auth schemes are stripped
before the spec is exposed to the LLM).

> ⚠️ **Trading places real orders.** `create_order` is a financially
> consequential tool. Read [Safety model](#safety-model) before pointing it at
> anything other than the sandbox.

---

## Install

```bash
pip install openwealth-mcp
```

Requires **Python ≥ 3.11** and a bearer token for an OpenWealth endpoint
(sandbox or custodian).

To install from source for development:

```bash
git clone https://github.com/OpenWealth/OpenWealth-MCP.git
cd OpenWealth-MCP
pip install -e ".[dev]"    # or: uv sync --extra dev
```

---

## Quickstart

Configure **each server separately** — each needs its own base URL and token.

**Claude Desktop / Claude Code** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "openwealth-custody": {
      "command": "openwealth-custody-mcp",
      "env": {
        "OPENWEALTH_CUSTODY_BASE_URL": "https://api.openwealth.synpulse8.com/api/custody-services/v3",
        "OPENWEALTH_BEARER_TOKEN": "<jwt>"
      }
    },
    "openwealth-trading": {
      "command": "openwealth-trading-mcp",
      "env": {
        "OPENWEALTH_TRADING_BASE_URL": "https://<host>/api/trading-services/v1",
        "OPENWEALTH_BEARER_TOKEN": "<jwt>"
      }
    },
    "openwealth-customer": {
      "command": "openwealth-customer-mcp",
      "env": {
        "OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL": "https://api.openwealth.synpulse8.com/api/customer-management/v2",
        "OPENWEALTH_BEARER_TOKEN": "<jwt>"
      }
    }
  }
}
```

**Cursor** (`.cursor/mcp.json`, or Settings → MCP for a global server):

```json
{
  "mcpServers": {
    "openwealth-custody": {
      "command": "openwealth-custody-mcp",
      "env": {
        "OPENWEALTH_CUSTODY_BASE_URL": "https://api.openwealth.synpulse8.com/api/custody-services/v3",
        "OPENWEALTH_BEARER_TOKEN": "<jwt>"
      }
    },
    "openwealth-trading": {
      "command": "openwealth-trading-mcp",
      "env": {
        "OPENWEALTH_TRADING_BASE_URL": "https://<host>/api/trading-services/v1",
        "OPENWEALTH_BEARER_TOKEN": "<jwt>"
      }
    },
    "openwealth-customer": {
      "command": "openwealth-customer-mcp",
      "env": {
        "OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL": "https://api.openwealth.synpulse8.com/api/customer-management/v2",
        "OPENWEALTH_BEARER_TOKEN": "<jwt>"
      }
    }
  }
}
```

Then run **MCP: Restart Servers** from the command palette and check that the
server shows as connected. Configure only the domain you have access to.

Sandbox JWTs often expire in about 60 seconds — refresh from the portal and
restart the server. Supply the token **without** the `Bearer ` prefix; the
client adds it.

Full client wiring, WSL specifics and troubleshooting live in
[`docs/mcp-clients.md`](docs/mcp-clients.md) and
[`docs/local-dev.md`](docs/local-dev.md).

---

## Configuration

All settings are environment variables prefixed `OPENWEALTH_`. A `.env` file in
the working directory is loaded automatically (and is gitignored — never commit
one). Host and credentials are never hard-coded.

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENWEALTH_CUSTODY_BASE_URL` | — | Custody API base URL including the path prefix, no trailing slash. Required when running the Custody server. `https://` is added if the scheme is missing. |
| `OPENWEALTH_TRADING_BASE_URL` | — | Trading API base URL including the path prefix, no trailing slash. Required when running the Trading server. |
| `OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL` | — | Customer Management API base URL including the path prefix, no trailing slash. Required when running the Customer Management server. |
| `OPENWEALTH_BEARER_TOKEN` | — | Access token **without** the `Bearer ` prefix. Required unless `OPENWEALTH_AUTH_HEADER` is set. |
| `OPENWEALTH_AUTH_HEADER` | — | Full `Authorization` header value; overrides `OPENWEALTH_BEARER_TOKEN`. |
| `OPENWEALTH_CORRELATION_ID` | generated | Fixed correlation id; otherwise a UUID per request. |
| `OPENWEALTH_TIMEOUT_SECONDS` | `120` | Read/write timeout in seconds (max 300). |
| `OPENWEALTH_CONNECT_TIMEOUT_SECONDS` | `10` | Connect timeout in seconds (max 120). |
| `OPENWEALTH_MAX_RETRIES` | `2` | Retries for transient failures (0–5). See [Safety model](#safety-model). |
| `OPENWEALTH_VERIFY_TLS` | `true` | Set to `false` only against a sandbox with a self-signed certificate. |
| `OPENWEALTH_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR`. JSON logs on stderr. |
| `OPENWEALTH_LOG_FILE` | — | Optional log file path (logs to both file and stderr). |

Startup fails fast if neither `OPENWEALTH_BEARER_TOKEN` nor `OPENWEALTH_AUTH_HEADER` is set.
The URL for each server is validated at startup — a missing URL prints a clear error and exits.

**Transport is stdio only.** HTTP transport and JWKS ingress are out of scope
in favour of a smaller surface.

---

## Tools

Every response is JSON with `status_code`, `correlation_id` and `data`
(plus `next_cursor` on paginated GETs). Errors return
`{"error": true, "error_code": "...", "message": "...", "retryable": bool}` — never a stack trace.

### Custody — `openwealth-custody-mcp`

| Tool | operationId | Endpoint |
|------|-------------|----------|
| `get_customers` | `getCustomers` | `GET /customers` |
| `get_customers_by_customer_id` | `getCustomersByCustomerId` | `GET /customers/{customerId}` |
| `get_customer_accounts_by_customer_id` | `getCustomerAccountsByCustomerId` | `GET /customers/{customerId}/accounts` |
| `get_customer_account_by_id` | `getCustomerAccountById` | `GET /customers/{customerId}/accounts/{accountId}` |
| `get_customer_position_by_customer_id` | `getCustomerPositionByCustomerId` | `GET /customers/{customerId}/positions` |
| `get_customer_position_by_id` | `getCustomerPositionById` | `GET /customers/{customerId}/positions/{positionId}` |
| `get_account_position_by_account_id` | `getAccountPositionByAccountId` | `GET /accounts/{accountId}/positions` |
| `get_account_position_by_id` | `getAccountPositionById` | `GET /accounts/{accountId}/positions/{positionId}` |
| `get_transaction_by_customer_id` | `getTransactionByCustomerId` | `GET /customers/{customerId}/transactions` |
| `get_transaction_by_transaction_id` | `getTransactionByTransactionId` | `GET /customers/{customerId}/transactions/{transactionId}` |

Listing positions and transactions requires a `date` (`YYYY-MM-DD`) — the
OpenAPI spec makes it mandatory.

### Trading — `openwealth-trading-mcp`

| Tool | operationId | Endpoint |
|------|-------------|----------|
| `list_customers` | `listCustomers` | `GET /customers` |
| `get_customer` | `getCustomer` | `GET /customers/{customerId}` |
| `list_accounts` | `listAccounts` | `GET /accounts` |
| `get_account` | `getAccount` | `GET /accounts/{accountId}` |
| `list_orders` | `listOrders` | `GET /orders` |
| `get_order` | `getOrder` | `GET /orders/{orderId}` |
| **`create_order`** ⚠️ | `createOrder` | `POST /orders` |
| `cancel_order` | `actionCancelOrder` | `POST /orders/{orderId}/actions/cancel` |
| `list_order_executions` | `listOrderExecutions` | `GET /orders/{orderId}/executions` |
| `get_order_execution` | `getOrderExecution` | `GET /orders/{orderId}/executions/{executionId}` |
| `list_order_states` | `listOrderStates` | `GET /orders/{orderId}/states` |
| `create_quote` | `createQuote` | `POST /quotes` |
| `list_event_subscriptions` | `listEventSubscriptions` | `GET /event-subscriptions` |
| `get_event_subscription` | `getEventSubscription` | `GET /event-subscriptions/{eventSubscriptionId}` |
| `create_event_subscription` | `createEventSubscription` | `POST /event-subscriptions` |
| `update_event_subscription` | `updateEventSubscription` | `PUT /event-subscriptions/{eventSubscriptionId}` |
| `delete_event_subscription` | `deleteEventSubscription` | `DELETE /event-subscriptions/{eventSubscriptionId}` |
| `list_event_subscription_notifications` | `listEventSubscriptionEventNotifications` | `GET /event-subscriptions/{eventSubscriptionId}/event-notifications` |

### Customer Management — `openwealth-customer-mcp`

| Tool | operationId | Endpoint |
|------|-------------|----------|
| `get_customers` | `getCustomers` | `GET /customers` |
| **`create_customer`** ⚠️ | `postCustomer` | `POST /customer-details` |
| `get_customer` | `getCustomerByCustomerId` | `GET /customers/{customerId}` |
| `get_customer_details` | `getCustomerDetailsByCustomerId` | `GET /customers/{customerId}/customer-details` |
| `get_persons` | `getPersons` | `GET /customers/{customerId}/persons` |
| **`create_person`** ⚠️ | `postPerson` | `POST /customers/{customerId}/person-details` |
| `get_person` | `getPersonByPersonId` | `GET /customers/{customerId}/persons/{personId}` |
| `get_person_details` | `getPersonDetailsByPersonId` | `GET /customers/{customerId}/person-details/{personId}` |
| `get_contacts` | `getContactDetailsByCustomerId` | `GET /customers/{customerId}/persons/{personId}/contacts` |
| `create_contact` | `postContactDetailsByCustomerId` | `POST /customers/{customerId}/persons/{personId}/contacts` |
| `get_contact` | `getContactDetailsByContactDetailID` | `GET /customers/{customerId}/persons/{personId}/contacts/{contactId}` |
| `update_contact` | `putContactDetailByContactDetailId` | `PUT /customers/{customerId}/persons/{personId}/contacts/{contactId}` |
| `delete_contact` | `deleteContactDetailsByContactDetailID` | `DELETE /customers/{customerId}/persons/{personId}/contacts/{contactId}` |
| `get_addresses` | `getAddressByCustomerId` | `GET /customers/{customerId}/persons/{personId}/addresses` |
| `create_address` | `postAddressByCustomerId` | `POST /customers/{customerId}/persons/{personId}/addresses` |
| `get_address` | `getAddressByAddressId` | `GET /customers/{customerId}/persons/{personId}/addresses/{addressId}` |
| `update_address` | `putAddressByCustomerId` | `PUT /customers/{customerId}/persons/{personId}/addresses/{addressId}` |
| `get_documents` | `getDocumentsByCustomerId` | `GET /customers/{customerId}/documents` |
| **`create_document`** ⚠️ | `postDocumentByCustomerId` | `POST /customers/{customerId}/document-details` |
| `get_document` | `getDocumentByDocumentId` | `GET /customers/{customerId}/documents/{documentId}` |
| `get_document_details` | `getDocumentDetailsByDocumentId` | `GET /customers/{customerId}/documents/{documentId}/document-details` |
| `get_kyc` | `getKycByCustomerId` | `GET /customers/{customerId}/persons/{personId}/kyc` |
| **`create_kyc`** ⚠️ | `postKyc` | `POST /customers/{customerId}/persons/{personId}/kyc` |
| `create_prospect_precheck` | `postProspect` | `POST /prospect-precheck` |
| `get_prospect_precheck` | `getPreCheck` | `GET /prospect-precheck/{temporaryId}` |
| `get_status` | `getStatusByTemporaryId` | `GET /status/{temporaryId}` |

### MCP resources

| URI | Content |
|-----|---------|
| `openwealth://specs/custody` | Custody tool/endpoint table (Markdown) |
| `openwealth://specs/custody.yaml` | Custody OpenAPI schema reference (server URLs and auth stripped) |
| `openwealth://specs/trading` | Trading tool/endpoint table with financial-impact notes |
| `openwealth://specs/trading.yaml` | Trading OpenAPI schema reference (server URLs and auth stripped) |
| `openwealth://specs/customer` | Customer Management tool/endpoint table with write-impact notes |
| `openwealth://specs/customer.yaml` | Customer Management OpenAPI schema reference (server URLs and auth stripped) |

---

## Safety model

- **`create_order` is never retried.** A duplicate order is a financial error,
  so a failed POST fails loudly rather than silently placing a second one.
- **Customer Management write tools are never retried.** `create_customer`,
  `create_person`, `create_contact`, `create_address`, `create_document`,
  `create_kyc` and `create_prospect_precheck` are not retried to avoid
  duplicate records at the custody bank.
- **Idempotent writes are retried** on 5xx: `cancel_order`, `create_quote`,
  `update_contact`, `update_address`, `PUT` and `DELETE`. GETs retry on
  408, 429 and 5xx with exponential backoff and ±20% jitter.
  The `Retry-After` header is honoured.
- **Tool annotations** (`readOnlyHint`, `destructiveHint`, `idempotentHint`) are
  set per tool, so MCP clients can require confirmation for writes.
- **Tokens are never tool arguments.** They come from the environment only, and
  are never echoed in tool results or logs.
- **Custody is read-only** by design. Only the Trading and Customer servers can mutate state.

Always confirm order details with a human before calling `create_order`.

---

## Development

```bash
uv sync --extra dev          # or: pip install -e ".[dev]"

uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy                  # strict
uv run pytest -q             # coverage gate: 84%
```

The same four gates run in CI on every push and pull request across Python 3.11,
3.12 and 3.13. `pre-commit install` wires ruff and mypy into your commits.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for full contribution guidelines.

---

## Documentation

| Where | What |
|-------|------|
| [`CHANGELOG.md`](CHANGELOG.md) | Release history |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Dev setup and contribution guidelines |
| [`docs/mcp-clients.md`](docs/mcp-clients.md) | MCP client configuration (Claude, Cursor, WSL) |
| [`docs/local-dev.md`](docs/local-dev.md) | Local development setup |
| [`docs/release.md`](docs/release.md) | Release and publishing process |
| [`specs/`](specs/) | Vendored OpenAPI definitions |
| [`SECURITY.md`](SECURITY.md) | Vulnerability reporting and secret handling |

---

## Scope

Custody is read-only (GET). Trading covers the full order lifecycle
(GET, POST, PUT, DELETE). Customer Management covers the full customer
onboarding and lifecycle (GET, POST, PUT, DELETE). HTTP transport, JWKS ingress
and a central MCP gateway are out of scope.

---

## License

[Apache-2.0](LICENSE)
