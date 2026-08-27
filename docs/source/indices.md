# Indices

Declaring `class Index` inside a document is enough for most projects. An index *object* is the
alternative, and it earns its keep in two situations: pointing several documents at one index, and
reusing one set of index settings across documents.

## Index objects

Import `Index` from this package — not from `opensearchpy`. This one applies the project-wide
[`OPENSEARCH_INDEX_SETTINGS`](settings.md#opensearch_index_settings) defaults, and its `.document()`
decorator registers the document for you:

```python
# documents.py

from django_opensearch_models import Document, Index

from .models import Car

cars = Index("cars")
cars.settings(number_of_shards=1, number_of_replicas=0)


@cars.document
class CarDocument(Document):
    class Django:
        model = Car
        fields = ["name", "color"]
```

:::{warning}
Do not stack `@registry.register_document` on top of `@cars.document`. The index object's decorator
already registers the document; applying both registers it twice.
:::

Either style produces the same index. Mixing them across a project is fine — the registry does not
care which one a given document used.

(rebuilding-without-downtime)=
## Rebuilding without downtime

`search_index --rebuild` deletes the index before recreating it. Searches issued in that window fail
against a missing index. To avoid that, rebuild behind an alias:

```console
$ ./manage.py search_index --rebuild --use-alias
```

The index name in your document becomes an **alias**. Each rebuild creates a fresh concrete index
named with a timestamp suffix, populates it, then atomically repoints the alias at it and deletes
the index it replaced. Searches keep hitting the old index until the moment the alias moves, and
never see an empty or half-populated one.

Keep the superseded index around — to roll back, or to inspect what changed — with:

```console
$ ./manage.py search_index --rebuild --use-alias --use-alias-keep-index
```

Nothing then deletes those old indices; that becomes your job.

:::{note}
Switching an existing index over to aliases is not automatic. A concrete index and an alias cannot
share a name, so the first `--use-alias` run against a name that is currently a real index will tell
you to delete it first. Plan for that on a live system.
:::

(post-index-signal)=
## The `post_index` signal

Sent after a bulk indexing operation finishes.

```python
from django.dispatch import receiver

from django_opensearch_models.signals import post_index


@receiver(post_index)
def log_indexing(sender, instance, actions, response, **kwargs):
    success, failed = response
    ...
```

`sender`
: The `Document` subclass that performed the indexing.

`instance`
: The document instance it was performed on.

`actions`
: The generator of bulk actions that was sent to OpenSearch.

`response`
: The return value of `opensearch-py`'s `bulk()` — a `(success_count, errors)` pair.

:::{warning}
This signal is **not** sent when indexing runs with `--parallel`, because `parallel_bulk()` has no
single completion point to fire it from. Do not rely on it for bookkeeping that must also hold for
parallel rebuilds.
:::

## Signal-driven updates

Index maintenance during normal ORM use is handled by a *signal processor*, chosen with
[`OPENSEARCH_SIGNAL_PROCESSOR`](settings.md#opensearch_signal_processor). Two ship with the library:

`RealTimeSignalProcessor`
: The default. Writes to OpenSearch inline, during the same request that saved the model. Simple,
  and immediately consistent — at the cost of putting a network round-trip to OpenSearch inside your
  write path, where a slow or unreachable cluster becomes a slow or failing request.

`CelerySignalProcessor`
: Hands the work to a Celery task instead. Requires the `celery` extra and a configured Celery app.
  Inside an atomic block it defers enqueuing to `transaction.on_commit()`, so a worker can never
  read a row before the transaction that wrote it commits.

Both are driven by `post_save`, `post_delete`, `pre_delete` and `m2m_changed`. Anything that does
not emit those signals — `QuerySet.update()`, `bulk_create()`, `QuerySet.delete()`, raw SQL — does
not reach the index.
