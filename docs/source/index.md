# django-opensearch-models

```{include} ../../README.md
:start-after: <!-- overview-start -->
:end-before: <!-- overview-end -->
```

## Supported versions

```{include} ../../README.md
:start-after: <!-- requirements-start -->
:end-before: <!-- requirements-end -->
```

## Where to start

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} {octicon}`rocket` Quickstart
:link: quickstart
:link-type: doc

Install the app, point it at a cluster, index your first model and search it.
:::

:::{grid-item-card} {octicon}`file-code` Documents
:link: documents
:link-type: doc

The `Document` class, the `Django` inner class, and the hooks that control what gets indexed.
:::

:::{grid-item-card} {octicon}`list-unordered` Fields
:link: fields
:link-type: doc

Field types, how Django model fields map onto them, and how to index relationships.
:::

:::{grid-item-card} {octicon}`stack` Indices
:link: indices
:link-type: doc

Index objects, zero-downtime rebuilds behind an alias, and the `post_index` signal.
:::

:::{grid-item-card} {octicon}`gear` Settings
:link: settings
:link-type: doc

Every Django setting this app reads, and what happens when you leave it out.
:::

:::{grid-item-card} {octicon}`terminal` Commands
:link: commands
:link-type: doc

The `search_index` management command in full.
:::

::::

```{toctree}
:hidden:
:maxdepth: 2

quickstart
documents
fields
indices
settings
commands
develop
```
