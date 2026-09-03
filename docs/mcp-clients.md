# Wiring MCP clients

How to connect an MCP client to the `openwealth-custody-mcp`,
`openwealth-trading-mcp` and `openwealth-customer-mcp` servers after
installing the package.

## Prerequisites

```bash
pip install openwealth-mcp      # or: uv add openwealth-mcp
```

You need a bearer token for each server domain you want to use. Sandbox JWTs
expire in ~60 seconds — refresh from the portal and restart the MCP server.

Supply the token **without** the `Bearer ` prefix; the client adds it.

---

## Claude Desktop / Claude Code

Edit `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`):

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

Restart Claude Desktop after editing.

---

## Cursor

Add to `.cursor/mcp.json` in your project root, or use Settings → MCP for a
global server:

```json
{
  "mcpServers": {
    "openwealth-custody": {
      "command": "python",
      "args": ["-m", "openwealth_mcp"],
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

Then **MCP: Restart Servers** from the command palette. Check the MCP panel to
confirm the servers show as connected.

---

## WSL / Windows

If the `openwealth-custody-mcp` binary is inside WSL but the MCP client runs on
Windows (or vice versa), use a `wsl` command wrapper:

```json
{
  "mcpServers": {
    "openwealth-custody": {
      "command": "wsl",
      "args": ["-e", "openwealth-custody-mcp"],
      "env": {
        "OPENWEALTH_CUSTODY_BASE_URL": "https://api.openwealth.synpulse8.com/api/custody-services/v3",
        "OPENWEALTH_BEARER_TOKEN": "<jwt>"
      }
    }
  }
}
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Server not connected | Wrong binary path | Run `which openwealth-custody-mcp` in the same shell; set full path |
| `ValueError: OPENWEALTH_BEARER_TOKEN … required` | Missing env | Set the relevant `OPENWEALTH_*_BASE_URL` and `OPENWEALTH_BEARER_TOKEN` |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Self-signed cert | Set `OPENWEALTH_VERIFY_TLS=false` |
| JWT expired | Sandbox tokens are short-lived | Refresh token from the sandbox portal and restart |
| Empty responses | Wrong base URL | Confirm the URL includes the API path prefix (e.g. `/api/custody-services/v3`) |

Enable debug logging to see full request/response details:
`OPENWEALTH_LOG_LEVEL=DEBUG` and optionally `OPENWEALTH_LOG_FILE=/tmp/mcp.log`.

### Smoke test

```bash
OPENWEALTH_CUSTODY_BASE_URL=https://... OPENWEALTH_BEARER_TOKEN=<jwt> \
  openwealth-custody-mcp --check
# prints: OK openwealth-custody v0.3.0 base_url=https://...

OPENWEALTH_TRADING_BASE_URL=https://... OPENWEALTH_BEARER_TOKEN=<jwt> \
  openwealth-trading-mcp --check
# prints: OK openwealth-trading v0.3.0 base_url=https://...

OPENWEALTH_CUSTOMER_MANAGEMENT_BASE_URL=https://... OPENWEALTH_BEARER_TOKEN=<jwt> \
  openwealth-customer-mcp --check
# prints: OK openwealth-customer v0.3.0 base_url=https://...
```
