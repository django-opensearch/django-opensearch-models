# django-opensearch-models

A Django integration for OpenSearch: declare a `Document` against a model, and the library builds
the index mapping, populates it, and keeps it in sync through Django's signals.

## Rules

- [Every change starts with a failing test](.claude/rules/tdd.md) — red, green; never write
  production code before a test that demands it.
- [Comments describe the present](.claude/rules/comments.md) — no comment, docstring or test name
  explains what the code used to do.
- [Documentation must track the API](.claude/rules/documentation.md) — any public-API change updates
  `docs/source/` in the same commit.

## Skills

Reach for these rather than improvising. Each one names the places that must change together,
which is where this codebase is easiest to get wrong.

| Skill | Use it when |
| --- | --- |
| `run-tests` | Running, debugging or adding tests. Covers the throwaway cluster and the `OPENSEARCH_REQUIRED` trap where a green run tests nothing. |
| `docs` | Writing or changing documentation, or after any user-visible change. |
| `release` | Cutting a release: version bump, changelog, tag, and the PyPI, Read the Docs and GitHub release publishing that follows. |
| `add-field-type` | Adding a field class. |
| `bump-support-matrix` | Changing supported Python, Django, opensearch-py or server versions. |

## Working on this repository

`main` is the default branch and is protected: changes land through a pull request, which needs one
approving review and a green `build and smoke-test artifacts` check. Branches must be up to date
before merging, so a merge to `main` puts open pull requests behind and they need updating. Only
squash merges are allowed, and the branch is deleted on merge.

## Layout

- `src/django_opensearch_models/` — the package. `documents.py` holds `Document` and the
  Django-field mapping table, `registries.py` the registry and `Django` inner-class handling,
  `signals.py` the signal processors, `apps.py` every setting the app reads.
- `tests/` — the suite. Unit tests must not need a server; server-dependent tests live in
  `tests/test_integration.py`.
- `docs/source/` — MyST Markdown, built with Sphinx, warnings are errors.
