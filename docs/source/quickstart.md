# Quickstart

This walks through indexing a single Django model end to end. It assumes you have an OpenSearch
cluster you can reach — if you do not,
[the official Docker instructions](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/docker/)
will get you one.

## Install

::::{tab-set}

:::{tab-item} pip
```console
$ pip install django-opensearch-models
```
:::

:::{tab-item} uv
```console
$ uv add django-opensearch-models
```
:::

:::{tab-item} With Celery
```console
$ pip install "django-opensearch-models[celery]"
```
Only needed to use `CelerySignalProcessor` — see
[`OPENSEARCH_SIGNAL_PROCESSOR`](settings.md#opensearch_signal_processor).
:::

::::

## The whole thing, end to end

```{include} ../../README.md
:start-after: <!-- example-start -->
:end-before: <!-- example-end -->
```

That is the entire happy path. The rest of this page explains the parts of it that bite.

## Where documents must live

The file has to be called `documents.py` and sit inside an installed app. On startup the app config
calls `autodiscover()`, which imports exactly that name from each app. A document declared anywhere
else is never imported, so it is never registered, never mapped and never updated — and nothing
raises an error to tell you.

## The connection setting is `OPENSEARCH`

:::{note}
Every setting this app reads is named `OPENSEARCH*` — see [Settings](settings.md). A setting name it
does not recognise is simply never read, leaving a cluster that is never contacted and an index that
stays empty.
:::

`OPENSEARCH` is handed straight to `opensearchpy.connections.configure()`, so anything that function
accepts works — TLS options, timeouts, and additional named connections beside `default`. See the
[opensearch-py documentation](https://opensearch-project.github.io/opensearch-py/) and
[Settings](settings.md#opensearch).

## The two inner classes

They divide cleanly, and it is worth keeping them straight:

`class Index`
: The OpenSearch side — index name, shards, replicas, analyzers.

`class Django`
: The Django side — which model feeds the index, which of its fields to index, and how updates
  behave.

[Documents](documents.md) covers every option on both, plus the hooks for computed values and for
controlling which objects get indexed at all.

## What keeps the index in sync

Once the index exists, ordinary ORM writes maintain it through Django's `post_save` and
`post_delete` signals. By default that write to OpenSearch happens inline, in the same request.

:::{important}
Queryset-level operations do not emit per-instance signals, so they never reach the index:
`QuerySet.update()`, `QuerySet.delete()`, `bulk_create()`, `bulk_update()` and raw SQL. After any of
those, re-index explicitly:

```console
$ ./manage.py search_index --populate --models myapp.Car
```
:::

To move indexing off the request path entirely, switch to the Celery processor — see
[`OPENSEARCH_SIGNAL_PROCESSOR`](settings.md#opensearch_signal_processor).

## Searching, and getting back to the ORM

`Document.search()` returns an `opensearch-py` search object, with the full query DSL behind it.
Iterating it yields OpenSearch hits — they carry only the fields you indexed, not model instances.

`.to_queryset()` converts a response into a real Django queryset when you need model behaviour:

```python
cars = CarDocument.search().filter("term", color="blue")[:30].to_queryset()
```

:::{note}
That costs one extra SQL query — the ids come out of the search response and are looked up with
`pk__in`. The queryset preserves the search ordering; pass `keep_order=False` if you would rather
order in the database.

Slice *before* calling `.to_queryset()`, as above. Without a slice you will pull back every match.
:::

## Next steps

- [Documents](documents.md) — computed fields, filtering what gets indexed, controlling the
  population queryset.
- [Fields](fields.md) — field types and indexing relationships.
- [Commands](commands.md) — rebuilding without downtime.
