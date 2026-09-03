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

---

## Recurring release process

The workflow supports two release paths:

### Path 1 — Automated via GitHub Actions UI (recommended)

Trigger the workflow manually from **GitHub → Actions → "Publish to PyPI" →
"Run workflow"** and choose:

| Input | Description |
|-------|-------------|
| `bump` | `patch` (default), `minor`, or `major` — computed from the current `__version__` |
| `version` | Optional exact version (e.g. `1.0.0`). When set, overrides `bump`. |

The workflow will:
1. Create a `release/vX.Y.Z` branch from `main`
2. Bump `__version__` in `src/openwealth_mcp/__init__.py`
3. Promote `[Unreleased]` in `CHANGELOG.md` to the new version with today's date
4. Commit the changes as `chore: release vX.Y.Z` on the release branch
5. Push the `vX.Y.Z` tag (this triggers the build + publish path automatically)
6. Open a PR `release/vX.Y.Z` → `main` for review and merge

Then, triggered by the tag push:

7. Build wheel + sdist, validate with `twine check`
8. Publish to TestPyPI, then to PyPI

Merge the auto-opened PR once the publish run succeeds.

> **Note:** the workflow never pushes directly to `main` — it always goes
> through a PR, respecting branch protection rules.

Or trigger it from the CLI:

```bash
# Patch bump (0.3.0 → 0.3.1)
gh workflow run publish.yml --field bump=patch

# Minor bump (0.3.0 → 0.4.0)
gh workflow run publish.yml --field bump=minor

# Exact version override
gh workflow run publish.yml --field version=1.0.0
```

### Path 2 — Manual tag push

Use this when you want full control over the commit history (e.g. you already
updated the CHANGELOG manually):

```
1. Bump __version__ in src/openwealth_mcp/__init__.py (e.g. "0.3.0" → "0.4.0")
2. Update CHANGELOG.md (move [Unreleased] entries to a new [0.4.0] section)
3. Commit: git commit -m "chore: release v0.4.0"
4. Tag:    git tag v0.4.0
5. Push:   git push && git push --tags
```

The `publish.yml` workflow fires automatically on the `v*` tag and skips the
bump job, going straight to build → TestPyPI → PyPI.

Watch progress in the repo → Actions → "Publish to PyPI".

---

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

---

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

---

## Workflow permissions note

The `bump-and-tag` job pushes a `release/vX.Y.Z` branch and a tag, and opens
a PR — it never pushes directly to `main`. This is compatible with protected
branch rules that require pull requests.

It requires **"Read and write permissions"** for `GITHUB_TOKEN` (Settings →
Actions → General → Workflow permissions). This is the default on most
repositories.

If your repository uses restricted token permissions, either:

- Change it to **"Read and write permissions"**, or
- Create a PAT with `contents: write` and `pull-requests: write` scopes, store
  it as a secret (e.g. `RELEASE_TOKEN`), and replace `secrets.GITHUB_TOKEN`
  with `secrets.RELEASE_TOKEN` in the `bump-and-tag` checkout step.

---

## Related

- Workflow: [`.github/workflows/publish.yml`](../.github/workflows/publish.yml)
- CI build step: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- Local dev: [`docs/local-dev.md`](local-dev.md)
