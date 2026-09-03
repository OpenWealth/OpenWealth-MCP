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

### 4. Allow GitHub Actions to create PRs and push tags

Settings → Actions → General → Workflow permissions:

- Select **"Read and write permissions"**
- Enable **"Allow GitHub Actions to create and approve pull requests"**

---

## Recurring release process

The release pipeline is split across three workflows:

```
release.yml        →   creates a "chore: release vX.Y.Z" PR against main
                                    │
                          (review + merge)
                                    │
tag-release.yml    →   detects the merge commit, pushes tag vX.Y.Z
                                    │
publish.yml        →   fires on the tag: build → TestPyPI → PyPI
```

The tag always points to a commit on `main`, so the repo history is always
consistent with the published artifact.

---

### Step 1 — Open a release PR

**Via GitHub UI:**  Actions → "Create Release PR" → Run workflow → choose:

| Input | Description |
|-------|-------------|
| `bump` | `patch` (default), `minor`, or `major` — computed from the current `__version__` |
| `version` | Optional exact version (e.g. `1.0.0`). When set, overrides `bump`. |

**Via CLI:**
```bash
gh workflow run release.yml --field bump=minor
gh workflow run release.yml --field version=1.0.0
```

The workflow creates a `release/vX.Y.Z` branch, bumps `__version__` and
`CHANGELOG.md`, and opens a PR with auto-merge enabled.

### Step 2 — Review and merge the PR

Check the diff (only `__init__.py` and `CHANGELOG.md` change). If auto-merge is
enabled and all required checks pass, the PR merges automatically. Otherwise
merge it manually.

### Step 3 — Tag and publish (automatic)

Once the PR lands on `main`:

1. `tag-release.yml` fires, reads the version from the commit message, and
   pushes tag `vX.Y.Z` pointing to the merge commit on `main`.
2. `publish.yml` fires on the tag:
   - Verifies `__version__` matches the tag
   - Builds wheel + sdist with `uv build`
   - Validates with `twine check`
   - Publishes to TestPyPI (environment `testpypi`)
   - Publishes to PyPI (environment `pypi`)

Watch progress in the repo → Actions → "Publish to PyPI".

---

## Manual release (bypass automation)

Use this when CI is unavailable or you need full control:

```bash
# 1. Edit src/openwealth_mcp/__init__.py — bump __version__
# 2. Edit CHANGELOG.md — promote [Unreleased] to [x.y.z]
git commit -am "chore: release v0.4.0"
git push                      # merge to main via PR or direct push
git tag v0.4.0
git push origin v0.4.0        # triggers publish.yml directly
```

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

## Related

- Release PR workflow: [`.github/workflows/release.yml`](../.github/workflows/release.yml)
- Tag workflow: [`.github/workflows/tag-release.yml`](../.github/workflows/tag-release.yml)
- Publish workflow: [`.github/workflows/publish.yml`](../.github/workflows/publish.yml)
- CI build step: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- Local dev: [`docs/local-dev.md`](local-dev.md)
