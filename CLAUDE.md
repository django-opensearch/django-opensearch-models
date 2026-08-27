# django-opensearch-models

A Django integration for OpenSearch: declare a `Document` against a model, and the library builds
the index mapping, populates it, and keeps it in sync through Django's signals.

## Rules

- [Comments describe the present](.claude/rules/comments.md) — no comment, docstring or test name
  explains what the code used to do.
- [Documentation must track the API](.claude/rules/documentation.md) — any public-API change updates
  `docs/source/` in the same commit.

## Skills

Reach for these rather than improvising; each encodes something this repo got wrong before.

| Skill | Use it when |
| --- | --- |
| `run-tests` | Running, debugging or adding tests. Covers the throwaway cluster and the `OPENSEARCH_REQUIRED` trap where a green run tests nothing. |
| `docs` | Writing or changing documentation, or after any user-visible change. |
| `release` | Cutting a release: version bump, changelog, tag, PyPI. |
| `add-field-type` | Adding a field class. |
| `bump-support-matrix` | Changing supported Python, Django, opensearch-py or server versions. |

## Layout

- `src/django_opensearch_models/` — the package. `documents.py` holds `Document` and the
  Django-field mapping table, `registries.py` the registry and `Django` inner-class handling,
  `signals.py` the signal processors, `apps.py` every setting the app reads.
- `tests/` — the suite. Unit tests must not need a server; server-dependent tests live in
  `tests/test_integration.py`.
- `docs/source/` — MyST Markdown, built with Sphinx, warnings are errors.
