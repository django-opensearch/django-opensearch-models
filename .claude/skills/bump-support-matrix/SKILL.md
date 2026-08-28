---
name: bump-support-matrix
description: Add or drop a supported Python, Django, opensearch-py or OpenSearch server version in django-opensearch-models. Names every file that encodes a version, since they drift silently. Use when asked to support a new version, drop an EOL one, or when a version claim looks wrong.
---

# Changing the support matrix

Versions are encoded in **seven** places. Nothing cross-checks most of them, so a partial bump
leaves the package claiming support it does not test: a README advertising a Django version
`tox.ini` has no environment for, or a CI matrix requesting an environment that does not exist.

Change them in one commit.

## The seven places

| File | What it encodes |
|---|---|
| `pyproject.toml` `requires-python` | Python floor |
| `pyproject.toml` `dependencies` | `django` and `opensearch-py` ranges |
| `pyproject.toml` `classifiers` | `Framework :: Django ::` and `Programming Language :: Python ::` |
| `tox.ini` `env_list` + the `dj*` factors | which combinations are actually tested |
| `.github/workflows/ci.yml` `matrix.include` | the six-leg pull-request slice |
| `.github/workflows/nightly.yml` `matrix` | the full cross product, plus the pinned server images |
| `README.md` "Requirements" | what users are told |

Also check: `.pre-commit-config.yaml` `default_language_version` when the Python floor moves, and
`.claude/skills/run-tests/SKILL.md` when the default server image changes.

**Dependabot cannot see the OpenSearch server images** — they live in workflow `run:` strings, not a
Dockerfile — so those are a manual bump.

## Rules

**Keep the cross product valid.** Django 6.x requires Python >= 3.12. The floor is `>=3.12` precisely
so every python × django pair is legal and neither `tox.ini` nor CI needs a single `exclude:`. If you
lower the Python floor below the highest Django's requirement, you reintroduce invalid cells that
either fail or quietly install a different Django than the one the job claims to test. Prefer raising
the floor over adding exclusions.

**Pin server images to a full patch version** (`2.19.6`, `3.8.0`), never a floating major or minor.
`runtests.py`'s `check_cluster()` asserts the cluster reports exactly `$OPENSEARCH_SERVER`, so a
floating tag turns into a confusing failure the day the image moves.

**The server version is deliberately not a tox factor.** It changes nothing about what tox installs,
so an `os219`/`os38` factor would double the environment count while producing byte-identical
environments. Which server was hit is recorded in the `COVERAGE_FILE` name, the CI job name, and
`check_cluster()`.

## Dropping a version

Dropping is breaking. Before you do it:

1. Check what `python-services` runs — **both** `develop` and any long-lived release branch.
2. Make sure a tag exists that still supports the version being dropped, so consumers have
   something to pin before `main` moves past them.
3. Use a `feat!:` commit with a `BREAKING CHANGE:` footer, and add a `### Changed` entry to
   `CHANGELOG.md` naming the tag to pin.

## Adding a version

Add the new leg to `tox.ini` and to the nightly cross product first, and only update the classifiers
and README once it actually passes. Claiming support before testing it is how the README came to
advertise Django 5.2 that CI never ran.

Consider whether the pull-request slice in `ci.yml` should change: it is meant to cover the oldest
supported combination, the newest, and one leg per (django, server) edge.

## Dependency floors are tested, not asserted

`tox -e lowest` installs the declared floors with `--resolution lowest-direct` rather than the
lockfile. If you raise or lower a floor in `dependencies`, run it:

```bash
uv run --frozen --no-default-groups --group tox tox run -e lowest
```

Prefer a permissive floor over a defensive one, but only as far as the API allows. `opensearch-py`
is floored at `>=3.1` because that is where the k-NN vector DSL field became `KnnVector`, mapping to
`knn_vector`; the 3.0 spelling `DenseVector` maps to `dense_vector`, a type OpenSearch has no handler
for. The floor stops short of `>=3.2`, which hard-pins `opensearch-protobufs==1.2.0`: forcing an
exact transitive pin on every consumer is a poor trade when the lockfile resolves 3.2 anyway.

## Verify

```bash
uv lock --upgrade && uv lock --check
uv run --no-project python .github/scripts/check_release_consistency.py
uv run --frozen --no-default-groups --group tox tox run        # every environment
uv run --frozen --no-default-groups --group tox tox run -e lowest
uvx check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/*.yml
```

Run the matrix against a throwaway container, one run at a time — see the `run-tests` skill.
