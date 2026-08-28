# Documents

A `Document` describes one OpenSearch index and the Django model that fills it. Everything this
library does — mapping generation, population, signal-driven updates — follows from that pairing.

```python
from django_opensearch_models import Document
from django_opensearch_models.registries import registry

from .models import Car


@registry.register_document
class CarDocument(Document):
    class Index:
        name = "cars"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Car
        fields = ["name", "color"]
```

Documents must live in a `documents.py` module inside an installed app. The app config calls
`autodiscover()` on startup and imports exactly that name; a document declared elsewhere is never
registered, never mapped and never updated, with no error to tell you so.

## The `Index` inner class

Describes the OpenSearch side of the pairing.

`name`
: The index name. Required.

`settings`
: A dict of index settings, passed to OpenSearch as-is — `number_of_shards`, `number_of_replicas`,
  custom analyzers and so on. See the
  [OpenSearch index settings reference](https://docs.opensearch.org/latest/api-reference/index-apis/update-settings/).

  :::{warning}
  These are applied *before* the project-wide
  [`OPENSEARCH_INDEX_SETTINGS`](settings.md#opensearch_index_settings), and the two are merged with
  the later call winning. A key present in both takes the **project-wide** value, not the one
  written here — setting `number_of_shards` globally silently overrides every document that also
  sets it.
  :::

For anything more involved than a name and some settings — sharing one index between documents, or
rebuilding behind an alias — use an [index object](indices.md) instead.

## The `Django` inner class

Describes which model feeds the index, and how.

`model`
: The Django model class. Required; registration fails with `ImproperlyConfigured` without it.

`fields`
: A list of model field names to index. Their OpenSearch types are derived from the Django field
  types — see [the mapping table](fields.md#how-django-fields-are-mapped). Naming a field here that
  you have also declared explicitly on the document raises `RedeclaredFieldError`, so the two can
  never silently disagree.

`related_models`
: Models whose changes should trigger a re-index of *this* document. Required whenever you embed
  data from another model with an `ObjectField` or `NestedField`, otherwise that embedded copy goes
  stale as soon as the related row changes. Pair it with `get_instances_from_related()`, below.

`ignore_signals`
: `False` by default. Set it to `True` to stop this document being updated automatically on
  `save()`/`delete()`, leaving population entirely to the management command. Useful for indices
  that are rebuilt on a schedule rather than maintained live.

`auto_refresh`
: Whether to ask OpenSearch to refresh the index after each write, making the change immediately
  visible to searches. Defaults to
  [`OPENSEARCH_AUTO_REFRESH`](settings.md#opensearch_auto_refresh); setting it here overrides that
  for this document only.

`queryset_pagination`
: Chunk size used when iterating the model during population. Without it the database driver's
  default applies, which for large tables can mean loading far more rows into memory at once than
  you want. The same value sizes the bulk requests sent to OpenSearch, on both the serial and the
  `--parallel` path.

## Computed and derived values

### A different attribute

Index the *string* form of a field rather than its raw value by pointing a document field at
another attribute or method with `attr`:

```python
# models.py


class Car(models.Model):
    ...

    def type_to_string(self):
        return dict(self._meta.get_field("type").choices).get(self.type, "")
```

```python
# documents.py

from django_opensearch_models import Document, fields


@registry.register_document
class CarDocument(Document):
    type = fields.TextField(attr="type_to_string")

    class Django:
        model = Car
        fields = ["name", "color"]  # `type` is declared on the document instead
```

`attr` is a dotted path resolved with Django template semantics — dictionary lookup, then attribute
lookup, then list-index lookup — so `attr="manufacturer.country.name"` works, and a callable found
along the way is called.

### A `prepare_` method

When a value needs real computation, define `prepare_<field>(self, instance)`. It is called
whenever that field is indexed and takes precedence over `attr`:

```python
class CarDocument(Document):
    summary = fields.TextField()

    def prepare_summary(self, instance):
        return f"{instance.name} ({instance.color})"
```

## Hooks

Every one of these is a method on your `Document` subclass.

`get_queryset(self)`
: The queryset used to populate the index. Defaults to `model._default_manager.all()`. Override it
  to narrow what gets indexed, or — more often — to avoid the N+1 that embedding related data
  otherwise causes:

  ```python
  def get_queryset(self):
      return super().get_queryset().select_related("manufacturer")
  ```

`get_indexing_queryset(self)`
: The iterator of instances used to populate the index, built from `get_queryset()` and chunked by
  `queryset_pagination`. The rows are drawn inside a transaction, because outside one PostgreSQL
  serves the underlying server-side cursor as `WITH HOLD` and materialises the whole result set to
  temporary storage before returning the first row. Override it only if you need a different
  traversal; if you do, keep the iteration itself inside the transaction, since a queryset is lazy
  and wrapping only its construction has no effect.

`should_index_object(self, obj)`
: Called per object during indexing; return `False` to skip it. Returns `True` by default. This is
  the right place for "only index published articles" logic, because unlike filtering in
  `get_queryset()` it also applies to signal-driven single-object updates.

`get_instances_from_related(self, related_instance)`
: Required when you use `related_models`. Given an instance of a related model, return the object or
  queryset of *this* document's model that needs re-indexing:

  ```python
  def get_instances_from_related(self, related_instance):
      if isinstance(related_instance, Manufacturer):
          return related_instance.car_set.all()
      if isinstance(related_instance, Ad):
          return related_instance.car
      return None
  ```

  :::{warning}
  Use `related_models` deliberately. One write to a widely-referenced model can fan out into
  re-indexing a very large number of documents, synchronously, inside the request that saved it.
  :::

`generate_id(cls, object_instance)`
: A classmethod returning the OpenSearch `_id` for an object. Defaults to the model's primary key.
  Override it to key documents by something else:

  ```python
  @classmethod
  def generate_id(cls, article):
      return article.slug
  ```

## Updating documents directly

`Document.update()` writes one instance, an iterable of them, or a queryset:

```python
CarDocument().update(car)
CarDocument().update(Car.objects.filter(color="red"))
CarDocument().update(car, action="delete")
CarDocument().update(qs, parallel=True, refresh=True)
```

`action` is `"index"` by default and accepts any OpenSearch bulk operation. `parallel=True` uses
`parallel_bulk()`; note that the {ref}`post_index <post-index-signal>` signal is not sent
in that mode.
