# Contributing to OpenWealth MCP

Thank you for your interest in contributing. This document covers the
development setup, quality gates, and pull-request conventions.

---

## Development setup

**Prerequisites:** Python ≥ 3.11, [uv](https://docs.astral.sh/uv/) (recommended)
or pip.

```bash
git clone https://github.com/synpulse-openwealth/openwealth-mcp.git
cd openwealth-mcp

# With uv (recommended)
uv sync --extra dev
pre-commit install

# Or with pip
pip install -e ".[dev]"
pre-commit install
```

Copy `.env.example` (if present) to `.env` and fill in your sandbox credentials.
The `.env` file is gitignored — never commit it.

---

## Quality gates

All four gates must be green before a pull request can merge. They run in CI
on every push across Python 3.11, 3.12, and 3.13.

```bash
uv run ruff check src tests       # linting
uv run ruff format --check src tests  # formatting
uv run mypy                       # type checking (strict)
uv run pytest -q                  # tests + coverage gate (84 %)
```

`pre-commit install` wires ruff and mypy into your commit hook so you get
fast feedback locally.

### Coverage

The coverage gate is at **84 %**. If your change reduces coverage, add tests.
The gate is set in `pyproject.toml` (`--cov-fail-under`). Do not lower it.

---

## Architecture

```
tools/ → service/ → OpenWealthHttpClient → OpenWealth API
```

- **Tools** (`tools/custody.py`, `tools/trading.py`): thin MCP adapters.
  They carry the `Annotated` schema the LLM sees and delegate every call to
  the service. No try/except — `invoke_tool` handles all error mapping.
- **Services** (`custody/service.py`, `trading/service.py`): one method per
  `operationId`. Own path construction, query-parameter assembly and input
  validation. No MCP or HTTP-transport knowledge.
- **Client** (`client.py`): shared async httpx wrapper with retry, jitter,
  `Retry-After` support and structured logging.

See [`wiki/decisions/clean-architecture-layers.md`](wiki/decisions/clean-architecture-layers.md)
for the full ADR.

---

## Pull request conventions

- **One logical change per PR.** Large refactors should be discussed in an
  issue first.
- **Commit messages** follow the conventional format:
  `<type>(<scope>): <short summary>` where `type` is one of
  `fix`, `feat`, `refactor`, `test`, `docs`, `chore`.
- **Breaking changes** must be called out in the PR description and in
  `CHANGELOG.md` under `### Changed` or `### Removed`.
- **New tools or API domains** require:
  - A service method with a docstring citing the `operationId`.
  - A tool adapter with `Annotated` schema and correct `ToolAnnotations`.
  - Tests covering the happy path and at least one error path.
  - A contract test entry in `tests/test_spec_contract.py`.
  - Updated tables in `README.md`.
- **Wiki updates** — after any meaningful architecture change, update
  `wiki/overview.md`, the relevant entity pages, `wiki/index.md`, and append
  a line to `wiki/log.md` (see [`AGENTS.md`](AGENTS.md)).

---

## Reporting issues

- **Bug reports and feature requests:** [GitHub Issues](https://github.com/synpulse-openwealth/openwealth-mcp/issues).
- **Security vulnerabilities:** see [`SECURITY.md`](SECURITY.md).

---

## Code of conduct

This project follows the
[Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
Please be respectful and constructive in all interactions.
