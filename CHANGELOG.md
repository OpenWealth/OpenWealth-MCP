# Changelog

All notable changes to this project are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.3.6] — 2026-09-04

---

## [0.3.5] — 2026-09-04

---

## [0.3.4] — 2026-09-04

---

## [0.3.3] — 2026-09-03

---

## [0.3.2] — 2026-09-03

---

## [0.3.1] — 2026-09-03

### Added

- **`openwealth-customer-mcp`** — new MCP server for the OpenWealth Customer
  Management API v2.0.6 with **26 tools** covering the full customer onboarding
  and lifecycle: customers, persons, contacts, addresses, documents, KYC, and
  prospect pre-checks (GET + POST + PUT + DELETE).
- **`OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL`** — new env variable for the
  Customer Management server base URL.
- **`specs/customerAPI.yaml`** — vendored OpenAPI YAML for Customer Management
  v2.0.6, served as `openwealth://specs/customer` and
  `openwealth://specs/customer.yaml` MCP resources.

---

## [0.3.0] — 2026-09-02

### Added

- **`OPENWEALTH_CUSTODY_BASE_URL`** and **`OPENWEALTH_TRADING_BASE_URL`** — each
  MCP server now has its own base URL variable. A single `.env` file can hold
  both. The URL for each server is resolved at startup via
  `Settings.base_url_for(service)`, printing a clear error and exiting with
  code 1 if the required variable is unset.

### Changed

- **BREAKING: `OPENWEALTH_BASE_URL` removed.** Replace it with
  `OPENWEALTH_CUSTODY_BASE_URL` (for the Custody server) and/or
  `OPENWEALTH_TRADING_BASE_URL` (for the Trading server) in your `.env` file
  and MCP client configuration (`claude_desktop_config.json`, `.cursor/mcp.json`).
- `OpenWealthHttpClient` now requires an explicit `base_url` keyword argument
  (previously read from `settings.base_url`).

### Removed

- **LLM wiki layer** (`wiki/`, `raw/`, `AGENTS.md`, `.cursor/rules/llm-wiki.mdc`)
  replaced by three plain Markdown pages under `docs/` (`mcp-clients.md`,
  `local-dev.md`, `release.md`). The wiki was an agent-maintained knowledge base
  that added 30 files to the repo with no value for package consumers.
- **Stale Docker runbook** (`wiki/runbooks/docker-cursor-mcp.md`) which documented
  a `Dockerfile` removed in v0.2.0 and the old package name `openwealth_ai_mcp`.

---

## [0.2.0] — 2026-09-02

### Added

- **Trading MCP server** (`openwealth-trading-mcp`) with 18 tools covering the
  full Order Placement API v3.0.1 lifecycle: customers, accounts, orders,
  executions, states, quotes, and event subscriptions.
- **`--check` flag** on both server entry points: validates settings and prints
  a one-line status without starting the stdio loop. Useful for deployment
  smoke tests.
- **`Retry-After` header support** in the HTTP client with ±20% jitter, so
  retries respect server-side rate-limit signals instead of always using
  exponential backoff.
- **Symmetric input validation** for Trading tools: `validate_id` on list-orders
  filter params, `validate_date` on `settlement_date` in `create_order`, and
  presence checks on every `allocations` entry.
- **`py.typed` marker** — the package now ships inline type information for
  downstream `mypy --strict` users.
- **`test_settings_docs_sync`** — asserts that the README config table and
  `Settings` field list are identical, so documentation can no longer silently
  diverge from code.
- **`test_spec_contract`** — parametrised contract test that verifies every
  `operationId` and path used by `CustodyService` and `TradingService` against
  the vendored OpenAPI specs.
- **`test_entrypoints`** — smoke tests for `main()` and `--check` on both
  servers, with `server.run` monkeypatched.
- **CI matrix** across Python 3.11, 3.12, and 3.13 (previously 3.13 only).
- **`pip-audit` job** in CI for supply-chain scanning.
- **Dependabot** configuration for pip and GitHub Actions weekly updates.
- **GitHub Actions pinned by commit SHA** to harden the supply chain.
- `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` links.

### Changed

- **Package renamed** from `openwealth-ai-mcp` / `openwealth_ai_mcp` to
  `openwealth-mcp` / `openwealth_mcp`. This is a **breaking change** for any
  existing import. Console scripts (`openwealth-custody-mcp`,
  `openwealth-trading-mcp`) are unchanged.
- **Single version source**: `__version__` in `src/openwealth_mcp/__init__.py`
  is the only declaration; `pyproject.toml` reads it dynamically via Hatch.
  Bumping one file bumps both.
- **License metadata** updated to PEP 639 form (`license = "Apache-2.0"`).
- **Package metadata** enriched with `authors`, `keywords`, `classifiers`
  (Python 3.11/3.12/3.13, Development Status :: 4 - Beta, Typing :: Typed),
  and `[project.urls]` (Homepage, Repository, Issues, Changelog).
- **`publish.yml`** tag trigger re-enabled (`push: tags: v*`); version check
  made conditional on tag context so manual dispatch no longer fails.
- **Coverage gate** raised from 80% to 84% to match the achieved baseline.
- **`OPENWEALTH_LOG_FILE` description** in README no longer says "Recommended
  with Docker" (Docker support removed).

### Removed

- **Docker support** (`Dockerfile`, `docker-compose.yml`, `.dockerignore`).
  The servers are distributed as a pip-installable library; Docker was an
  optional deployment target that added maintenance cost without proportional
  value for the current user base.
- **`openwealth-mcp` console script alias** (was a duplicate of
  `openwealth-custody-mcp` and ambiguous with two servers present).
- **`IMPROVEMENT-PLAN.md`** from the repository root (absorbed into
  `CHANGELOG.md` and GitHub issues).
- **Junk files** (`.coverage`, `_customers_dump.json`, `.tmp_*.py`, `logs/`)
  from the working tree; `.gitattributes` added to enforce LF line endings.

### Fixed

- **`mypy` strict failures** in `tools/trading.py`: `invoke_tool` now takes
  `Awaitable[str]` instead of `Any`, matching the custody implementation.
- **README config table** was documenting eight env vars that no longer exist
  in `Settings` (`OPENWEALTH_ENV`, `OPENWEALTH_TRANSPORT`, etc.) and had the
  wrong default for `OPENWEALTH_TIMEOUT_SECONDS` (30 vs 120 in code).
- **Unused dead code** removed: `TypeVar("_T")` in `tools/custody.py`,
  `peek_client()` in both `app.py` files.

---

## [0.1.0] — 2026-08-10

Initial release of the Custody MCP server.

- 10 read-only GET tools covering Custody Services API v3.2.0.
- FastMCP over stdio with clean `tools → service → HTTP client` layering.
- Pydantic-validated settings; structured JSON error envelopes.
- Vendored OpenAPI spec served as MCP resource.

[Unreleased]: https://github.com/OpenWealth/OpenWealth-MCP/compare/v0.3.6...HEAD
[0.3.6]: https://github.com/OpenWealth/OpenWealth-MCP/compare/v0.3.5...v0.3.6
[0.3.5]: https://github.com/OpenWealth/OpenWealth-MCP/compare/v0.3.3...v0.3.5
[0.3.4]: https://github.com/OpenWealth/OpenWealth-MCP/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/OpenWealth/OpenWealth-MCP/compare/v0.3.2...v0.3.3
[0.3.0]: https://github.com/synpulse-openwealth/openwealth-mcp/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/synpulse-openwealth/openwealth-mcp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/synpulse-openwealth/openwealth-mcp/releases/tag/v0.1.0
