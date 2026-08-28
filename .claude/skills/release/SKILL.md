---
name: release
description: Cut a django-opensearch-models release - bump the version, date the changelog section, tag and let CI publish to GitHub and PyPI. Use whenever asked to release, tag, bump the version, or prepare a version for downstream consumption.
---

# Cutting a release

The tag is the deliverable. `python-services` pins this package as a git dependency with
`tag = "..."`, and the same tag push is what drives the GitHub release and the PyPI upload -- so
getting the tag wrong is the one mistake with no clean recovery.

## The rule that matters

**Tags are unprefixed.** `1.1.0`, never `v1.1.0`. The `release.yml` trigger pattern and the
`pypi` environment's tag rule both assume it, and a `v`-prefixed tag simply does not trigger the
release workflow.

## The version lives in exactly one place

`pyproject.toml` `project.version`. Nothing else should contain a version literal:

- `src/django_opensearch_models/__init__.py` derives `__version__` from installed distribution
  metadata.
- `docs/source/conf.py` reads it the same way.

If you find yourself editing a second version literal, that is the bug — fix the duplication rather
than keeping the two in sync. Two literals that must agree will eventually disagree, and a version
the package does not actually have is worse than no version at all.

## Steps

1. **Confirm the branch is green**, including both signal processors. See the `run-tests` skill.

2. **Bump `project.version`** in `pyproject.toml`.

3. **Date the changelog section.** In `CHANGELOG.md`, turn `## [Unreleased]` into
   `## [1.1.0] - YYYY-MM-DD`, add a fresh empty `## [Unreleased]` above it, and update the link
   definitions at the bottom.

   Only list what actually shipped. A changelog claiming unshipped fixes is worse than no changelog.

4. **Check consistency locally** before pushing anything:
   ```bash
   uv run --no-project python .github/scripts/check_release_consistency.py --tag 1.1.0
   ```
   This is the same gate `release.yml` runs. It refuses a tag that does not match `project.version`,
   and refuses to cut a release from an undated `[Unreleased]` section.

5. **Commit, tag, push:**
   ```bash
   git tag -a 1.1.0 -m "django-opensearch-models 1.1.0"
   git push origin main
   git push origin 1.1.0
   ```

6. **`release.yml` builds on the tag push.** Its `build` job re-runs the consistency check, builds,
   verifies the shipped `test` subpackage survived packaging, smoke-installs the wheel, checks the
   installed version equals the tag, and attaches build provenance. Two jobs then fan out from it,
   both consuming the artifacts it produced rather than rebuilding:

   - `pypi` uploads them to PyPI.
   - `github-release` creates the GitHub release **as a draft**, with that version's changelog
     section as the notes.
   - `docs` runs after `pypi`, activates the tag on Read the Docs and builds it, polling the build
     to completion so a documentation failure fails the release.

7. **Publish the draft release by hand** once the `pypi` job is green. Releases page -> the draft ->
   *Publish release*. This is the last step; until you click it the release is unlisted, so a failed
   upload never leaves a public release pointing at a version PyPI does not have.

## PyPI publishing

Authentication is [trusted publishing](https://docs.pypi.org/trusted-publishers/) -- OIDC, no API
token stored anywhere. The `pypi` job mints a short-lived token that PyPI accepts only for this
repository, this workflow filename and the `pypi` GitHub environment. Renaming `release.yml` or the
environment breaks publishing until the trusted-publisher entry on PyPI is updated to match.

The publisher is registered on PyPI against four values -- owner `django-opensearch`, repository
`django-opensearch-models`, workflow `release.yml`, environment `pypi`. Change any of them and
publishing stops until the entry on PyPI is updated to match. Renaming the repository does not
break it, because PyPI matches on the repository *name*, not its numeric id.

The `pypi` environment restricts deployment to tags matching `[0-9]*.[0-9]*.[0-9]*`, so no branch
push can reach the publish job.

:warning: **That field is a glob, not a regex.** `.` is already literal, so escaping it as `\.`
matches a backslash; `+` is a literal plus, not a quantifier. Three patterns in this project look
alike and are not:

| Where | Syntax | Pattern |
| --- | --- | --- |
| `pypi` environment tag rule | glob | `[0-9]*.[0-9]*.[0-9]*` |
| `release.yml` `on: push: tags:` | glob | `[0-9]+.[0-9]+.[0-9]+*` |
| Read the Docs automation rule | **regex** | `^[0-9]+\.[0-9]+\.[0-9]+` |

PyPI rejects a re-upload of a version that already exists. If the `pypi` job fails after a partially
successful upload, cut a new patch version rather than trying to replace the files.

## Before dropping supported versions

A release that drops a Python, Django or opensearch-py version is breaking for someone. Check what
`python-services` is on first — both `develop` and any long-lived release branch — and make sure the
version they need is reachable by a tag they can pin before `main` moves past it.

Mark such a release with a `feat!:` commit and a `BREAKING CHANGE:` footer.

## If a release goes wrong

Do not force-push or move a tag that has been consumed — a downstream `uv.lock` records the resolved
commit, and moving the tag under it is worse than any bug. Cut a new patch version instead.
