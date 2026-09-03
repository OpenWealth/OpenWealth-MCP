# Local development

```bash
pip install -e ".[dev]"
# or: uv sync --extra dev
# create local .env (gitignored) with per-service URLs + OPENWEALTH_BEARER_TOKEN
ruff check src tests
mypy
pytest -q              # coverage gate 84%
python -m openwealth_mcp   # stdio MCP — for Cursor, not interactive typing
```

Env vars: see README.

- `OPENWEALTH_CUSTODY_BASE_URL` — required for the Custody server.
- `OPENWEALTH_TRADING_BASE_URL` — required for the Trading server.
- `OPENWEALTH_BEARER_TOKEN` is always required.
- `OPENWEALTH_VERIFY_TLS=false` to disable TLS for local sandbox with self-signed certs.
- Logs are JSON on stderr (optional rotating `OPENWEALTH_LOG_FILE`).

Both URLs can live in the same `.env` file; each server only reads its own.

MCP client wiring: command `openwealth-custody-mcp` (or `python -m openwealth_mcp`),
`cwd` = project root (loads `.env`), no extra env vars needed beyond URL + token.

Smoke test your settings without starting the server:

```bash
openwealth-custody-mcp --check
openwealth-trading-mcp --check
```

See also: [`docs/mcp-clients.md`](mcp-clients.md) for full client wiring details.
