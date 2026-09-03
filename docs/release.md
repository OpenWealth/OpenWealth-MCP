# Publish to PyPI

One-time setup + recurring release process for `openwealth-mcp` on PyPI.

## One-time setup (human steps)

These steps cannot be automated; do them once per registry (PyPI + TestPyPI).

### 1. Create PyPI accounts / org

- Go to https://pypi.org → create an account or use the `synpulse-openwealth` org.
- Do the same on https://test.pypi.org (separate account/org).
- Enable 2FA on both accounts.

### 2. Configure Trusted Publishers (no API token needed)

On **TestPyPI** → your account → Publishing tab → "Add a new pending publisher":

| Field | Value |
|-------|-------|
| PyPI Project Name | `openwealth-mcp` |
| Owner | `synpulse-openwealth` |
| Repository | `openwealth-mcp` |
| Workflow filename | `publish.yml` |
| Environment name | `testpypi` |

Repeat the same on **PyPI** with Environment name `pypi`.

Once the first upload succeeds the project is created and the "pending" publisher
becomes a normal publisher automatically.

### 3. Create GitHub Environments

In the GitHub repo → Settings → Environments:

- `testpypi`: no required reviewers (auto-publish on every tag)
- `pypi`: add required reviewer(s) for extra protection, or leave open for fully
  automatic production releases

The environment names must match those configured on PyPI/TestPyPI above.

## Recurring release process

```
1. Bump __version__ in src/openwealth_mcp/__init__.py (e.g. "0.3.0" → "0.4.0")
2. Update CHANGELOG.md (move [Unreleased] entries to a new [0.4.0] section)
3. Commit: git commit -m "chore: release v0.4.0"
4. Tag:    git tag v0.4.0
5. Push:   git push && git push --tags
```

The `publish.yml` workflow fires automatically on the `v*` tag:

1. Checks that the tag matches the installed package version (skipped on manual dispatch)
2. Builds wheel + sdist with `uv build`
3. Validates with `twine check dist/*`
4. Publishes to **TestPyPI** first (environment `testpypi`)
5. Then publishes to **PyPI** (environment `pypi`)

Watch progress in the repo → Actions → "Publish to PyPI".

## Verify after release

```bash
# TestPyPI (allow a few minutes for index propagation)
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ openwealth-mcp==<version>

# PyPI
pip install openwealth-mcp==<version>
openwealth-custody-mcp --check
openwealth-trading-mcp --check
```

Check https://pypi.org/project/openwealth-mcp/ for the public page.

## Emergency manual publish

If CI is broken and a hotfix must ship:

```bash
uv build
uv run --with twine twine check dist/*
# Requires a PyPI API token saved as TWINE_USERNAME=__token__ TWINE_PASSWORD=<token>
uv run --with twine twine upload dist/*
```

Never commit the API token. Generate a short-lived project-scoped token from
PyPI account settings and delete it after use.

## Related

- Workflow: [`.github/workflows/publish.yml`](../.github/workflows/publish.yml)
- CI build step: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- Local dev: [`docs/local-dev.md`](local-dev.md)
