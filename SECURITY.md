# Security Policy

## Supported versions

Security fixes are applied to the latest release on the `master` branch.

| Version | Supported |
|---------|-----------|
| 0.2.x   | ✅ |
| < 0.2   | ❌ (upgrade) |

---

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Use [GitHub private vulnerability reporting](https://github.com/synpulse-openwealth/openwealth-mcp/security/advisories/new)
to report suspected issues confidentially. GitHub will notify the maintainers
and keep the report private until a fix is released.

Include in your report:

- A description of the issue and its impact
- Steps to reproduce (proof of concept if available)
- Affected version or commit hash

We will acknowledge receipt within 5 business days and coordinate a fix and
disclosure timeline with you before any public announcement.

---

## Secret handling

- Never commit `.env`, tokens, or client secrets to the repository.
- Prefer short-lived credentials and secret injection via environment variables
  or a secrets manager.
- MCP tool results must not echo raw `Authorization` headers or bearer tokens.
- Never accept tokens as MCP tool arguments — always supply them via
  `OPENWEALTH_BEARER_TOKEN` or `OPENWEALTH_AUTH_HEADER`.
- The `RedactingFilter` in `logging_config.py` strips bearer tokens from log
  lines; do not remove or weaken it.
