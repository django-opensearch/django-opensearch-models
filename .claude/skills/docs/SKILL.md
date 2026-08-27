---
name: docs
description: Write or change the django-opensearch-models documentation - the Sphinx site under docs/source and the README. Use whenever asked to document something, fix or add docs, or after changing anything a user of the library can see.
---

# Documentation

The docs are **Sphinx + MyST Markdown**, themed with **furo**, published on Read the Docs. There is
no reStructuredText: `source_suffix` registers `.md` only, deliberately.

## The rule

**Any change to the public API changes the documentation in the same commit.** Public API means
anything a consumer can touch: a setting name or default, a `Document` hook, the `Django`/`Index`
inner-class options, a field class, a signal or its arguments, a `search_index` flag, the supported
version matrix.

A PR that adds a setting and not its entry in `settings.md` is incomplete. The docs went years
telling people to configure `OPENSEARCH_DSL` — a setting the code has never read — because nobody
held to this.

## Where things go

| Page | Holds |
| --- | --- |
| `index.md` | Landing page. Pulls its overview and version table from `README.md`. |
| `quickstart.md` | The end-to-end happy path, and the things that bite while doing it. |
| `documents.md` | `Document`, the `Index`/`Django` inner classes, every overridable hook. |
| `fields.md` | Field classes, the Django-field mapping table, relationships, analyzers. |
| `indices.md` | Index objects, alias rebuilds, `post_index`, signal processors. |
| `settings.md` | One section per setting. Reference, not tutorial. |
| `commands.md` | Every `search_index` action and flag, plus recipes. |
| `develop.md` | Contributing: environment, tests, the matrix. |

## Never duplicate between README and docs

The README is the single source for the project overview, the supported-version table and the
end-to-end example. The docs *include* those regions rather than restating them:

```markdown
```{include} ../../README.md
:start-after: <!-- overview-start -->
:end-before: <!-- overview-end -->
```
```

The marker pairs in `README.md` are `overview`, `requirements` and `example`. If you change what
lives inside them, check `index.md` and `quickstart.md` still read correctly around the seam. Never
copy text out of a marked region into a docs page.

## Verify before claiming

Read the source before documenting behaviour rather than trusting a sentence that is already
there. Settings live in `apps.py` and `search_index.py`, the `Django` options in
`registries.py::register_document`, the hooks in `documents.py`, the field mapping table in
`documents.py::model_field_class_to_field_class`.

## Building

```bash
uv run --frozen --no-default-groups --group tox tox run -e docs
```

Warnings are errors, here and on Read the Docs. A broken cross-reference fails the build.

- Cross-document links to a heading containing backticks or underscores are fragile. Add an explicit
  target and use `{ref}`:
  ```markdown
  (post-index-signal)=
  ## The `post_index` signal
  ```
  then `{ref}`post_index <post-index-signal>`` from anywhere.
- `ruff format` formats Python code blocks inside Markdown. Run `tox -e lint` after editing samples,
  and keep samples valid Python — a snippet that cannot be parsed will fail the format check.
- Check external links with
  `uv run --frozen --no-default-groups --group docs python -m sphinx -b linkcheck docs/source /tmp/lc`.

## House style

- Say what breaks, not just what to do. `:::{warning}` and `:::{important}` blocks exist for the
  traps — bulk querysets not emitting signals, `post_index` being silent under `--parallel`,
  `.to_queryset()` costing a query.
- Prefer a short prose sentence over a bulleted fragment. Definition lists suit reference material.
- This project targets OpenSearch and `opensearch-py`, and the documentation should read as
  though it has never targeted anything else. Do not link to another search engine's
  documentation or name its libraries as though they were a dependency here. The document base
  class is `Document`, the field base class is `OSField`. `NOTICE` is the single place any prior
  project is named; it carries the attribution the Apache-2.0 terms require to be retained, and
  nothing else should reproduce it.
