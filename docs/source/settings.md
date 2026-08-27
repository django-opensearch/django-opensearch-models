# Settings

Every setting this app reads, in the order you are likely to need them. All are optional except
`OPENSEARCH`.

## `OPENSEARCH`

**Required.** Connection configuration, passed straight to
`opensearchpy.connections.configure()`:

```python
OPENSEARCH = {
    "default": {
        "hosts": "localhost:9200",
        "http_auth": ("username", "password"),
    },
}
```

Declare additional named connections alongside `default` to talk to more than one cluster. Anything
`configure()` accepts is valid here — TLS options, timeouts, connection classes; see the
[opensearch-py documentation](https://opensearch-project.github.io/opensearch-py/).

The app raises `AttributeError` on startup if this setting is missing, which is deliberate: a
default of `localhost:9200` would let a misconfigured deployment start up and quietly index nothing.

## `OPENSEARCH_AUTOSYNC`

**Default:** `True`

Whether model changes propagate to OpenSearch at all. Setting it to `False` disables every automatic
update project-wide, leaving the management commands as the only way to populate an index.

The usual reason to turn it off is tests, where you want the ORM without a live cluster behind it.
To disable syncing for one document rather than all of them, use `Django.ignore_signals` instead —
see [Documents](documents.md#the-django-inner-class).

## `OPENSEARCH_SIGNAL_PROCESSOR`

**Default:** `"django_opensearch_models.signals.RealTimeSignalProcessor"`

The dotted path to the class that translates Django signals into index updates.

```python
OPENSEARCH_SIGNAL_PROCESSOR = "django_opensearch_models.signals.CelerySignalProcessor"
```

`RealTimeSignalProcessor`
: Updates the index inline, in the request that made the change.

`CelerySignalProcessor`
: Enqueues a Celery task instead. Needs the `celery` extra installed and a Celery app configured in
  the project — see
  [Using Celery with Django](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html).
  Deletes are handled by capturing the document id before the row disappears, and enqueuing inside an
  atomic block is deferred to `transaction.on_commit()` so a worker cannot read a row before it is
  committed.

Subclass either one for custom behaviour, such as routing updates to a specific queue.

## `OPENSEARCH_AUTO_REFRESH`

**Default:** `True`

Whether to ask OpenSearch to
[refresh](https://docs.opensearch.org/latest/api-reference/index-apis/refresh/) an index after each
write, making the change visible to searches immediately rather than at the next refresh interval.

Convenient, and expensive under sustained write load — a refresh per save forces a great deal of
segment churn. Set it to `False` in write-heavy projects and let OpenSearch refresh on its own
schedule, or override it per document with `Django.auto_refresh`.

## `OPENSEARCH_INDEX_SETTINGS`

**Default:** `{}`

Index settings applied to every index this app creates:

```python
OPENSEARCH_INDEX_SETTINGS = {"number_of_shards": 3}
```

These are applied at registration, after each document's own `Index.settings`, and the two dicts are
merged with the later write winning.

:::{warning}
A key set here **overrides** the same key on an individual document, which is the opposite of what
"default" usually implies. With `OPENSEARCH_INDEX_SETTINGS = {"number_of_shards": 3}`, a document
asking for `number_of_shards: 1` gets 3. Keys this setting does not mention are left alone, so
per-document values survive for everything else.

Set only what you genuinely want to force everywhere; anything a document should be able to choose
for itself does not belong here.
:::

## `OPENSEARCH_PARALLEL`

**Default:** `False`

Whether `search_index --populate` and `--rebuild` use `parallel_bulk()` by default. Equivalent to
passing `--parallel` every time; `--no-parallel` overrides it for a single run.

:::{warning}
Parallel indexing opens several database connections at once. SQLite in particular does not
cope. It also suppresses the {ref}`post_index <post-index-signal>` signal.
:::
