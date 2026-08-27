# Contributing

We are glad to welcome any contributor.

Report bugs or propose enhancements through the
[GitHub issue tracker](https://github.com/django-opensearch/django-opensearch-models/issues).
The code lives at
<https://github.com/django-opensearch/django-opensearch-models>.

## Getting set up

The project uses [uv](https://docs.astral.sh/uv/). It manages the virtual environment, the
interpreter and the lockfile, so there is nothing to create by hand:

```console
$ uv sync --dev
```

## Running the tests

Most of the suite runs without a server:

```console
$ uv run python runtests.py
$ uv run python runtests.py tests.test_fields    # a single module
```

The integration tests need a running OpenSearch cluster. Use a **throwaway container**, never a
development cluster — the tests create, populate and delete indices, and `OSTestCase` mutates the
global document registry:

```console
$ docker run -d --name dosm-test-os -p 9201:9200 \
    -e discovery.type=single-node \
    -e DISABLE_INSTALL_DEMO_CONFIG=true \
    -e "plugins.security.disabled=true" \
    opensearchproject/opensearch:3.8.0
$ export OPENSEARCH_URL=http://127.0.0.1:9201 OPENSEARCH_REQUIRED=1
$ uv run python runtests.py
```

:::{important}
Set `OPENSEARCH_REQUIRED=1`. The integration tests are guarded by
`unittest.skipUnless(is_os_online())`, so without it an unreachable cluster produces a **fully green
run that executed zero integration tests**.
:::

Run one thing at a time against a cluster. `OSTestCase` renames indices in the registry during
`setUp` and strips the suffix in `tearDown`, so two concurrent runs collide and produce accumulated
suffixes such as `car_index_os_test_os_test` — failures that look like code bugs and are not.
That also rules out `tox run-parallel`.

## The signal processors

There are two, and CI runs both. A change that only passes one is not finished:

```console
$ uv run python runtests.py
$ uv run python runtests.py --signal-processor celery
```

## The full matrix

[tox](https://tox.wiki) drives every supported combination of Python, Django and OpenSearch server:

```console
$ uv run --frozen --no-default-groups --group tox tox run             # everything
$ uv run --frozen --no-default-groups --group tox tox run -e py314-dj61
```

Other environments: `lint`, `build`, `docs`, `coverage`, and `lowest`, which installs the declared
dependency floors instead of the lockfile.

## Working on the documentation

The docs are [Sphinx](https://www.sphinx-doc.org/) with
[MyST](https://myst-parser.readthedocs.io/) Markdown sources, themed with
[furo](https://pradyunsg.me/furo/). Every page under `docs/source/` is `.md`; reStructuredText is
not registered as a source suffix, so a `.rst` file added there is silently ignored.

### Live preview

The fastest loop. It builds the site, serves it, and rebuilds on every save:

```console
$ uv run --frozen --no-default-groups --group tox tox run -e docs-serve
```

Then open <http://127.0.0.1:8000>. The browser reloads itself when a build finishes.

### One-off build

What CI and Read the Docs run:

```console
$ uv run --frozen --no-default-groups --group tox tox run -e docs
```

:::{important}
Warnings are errors (`-W`), here and on Read the Docs. A broken cross-reference, a heading that no
longer matches the anchor pointing at it, or a `toctree` entry for a file that does not exist all
fail the build rather than quietly degrading the published site. Fix the first warning and rebuild;
`--keep-going` means the rest are reported in the same run.
:::

### Checking links

External links are not checked by the normal build. Run the link checker before changing many of
them:

```console
$ uv run --frozen --no-default-groups --group tox tox run -e docs-linkcheck
```

It reports `broken` for dead links and `redirect` for ones that have moved. Redirects are not
failures, but a permanent one is worth following in the source.

### Code samples are linted

`ruff format` formats Python code blocks inside Markdown, so samples are held to the same style as
the source tree. A sample that is not valid Python fails `tox -e lint`:

```console
$ uv run --frozen --no-default-groups --group tox tox run -e lint
```

Write samples that would actually run. If a snippet needs an elision, use `...` — it parses.

### The README is the single source

The project overview, the supported-version table and the end-to-end example live in `README.md`
between HTML comment markers, and the docs include those regions rather than restating them:

````markdown
```{include} ../../README.md
:start-after: <!-- overview-start -->
:end-before: <!-- overview-end -->
```
````

The marker pairs are `overview`, `requirements` and `example`. Sphinx tracks the dependency, so
editing `README.md` rebuilds the pages that include it — `index.md` and `quickstart.md` — and
`docs-serve` watches it too. Never copy text out of a marked region into a page; change it in the
README and both surfaces follow.

### Cross-references

Links between pages are ordinary relative Markdown links: `[Settings](settings.md)`, or
`[Settings](settings.md#opensearch_autosync)` for a heading.

Headings containing backticks or underscores generate anchors that are easy to get wrong. Give
those an explicit target instead and reference it with `{ref}`:

```markdown
(post-index-signal)=
## The `post_index` signal
```

then from any page:

```markdown
{ref}`post_index <post-index-signal>`
```

### Before you push

The documentation must match the API. If your change adds, renames or alters a setting, a `Document`
hook, a field class, a signal or a `search_index` flag, update the page that documents it in the
same commit — see the pages listed in the table below.

| Page | Covers |
| --- | --- |
| `quickstart.md` | The end-to-end happy path and its common traps. |
| `documents.md` | `Document`, the `Index`/`Django` inner classes, the overridable hooks. |
| `fields.md` | Field classes, the Django-field mapping table, relationships, analyzers. |
| `indices.md` | Index objects, alias rebuilds, `post_index`, signal processors. |
| `settings.md` | One section per setting. |
| `commands.md` | Every `search_index` action and flag. |

## Known gaps

- Support for `--using` (a second OpenSearch cluster) in the management commands.
- Management commands for mapping-level operations, such as `update_mapping`.
- Generating `ObjectField` / `NestedField` properties from a `Document` class.
- More examples, and better documentation for testing with `OSTestCase`.
