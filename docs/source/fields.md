# Fields

Document fields are thin subclasses of the `opensearch-py` field types. They add one thing: knowing
how to pull a value off a Django model instance. Everything a plain `opensearch-py` field accepts —
analyzers, multi-fields, index options — works here too.

```python
from django_opensearch_models import Document, fields


@registry.register_document
class CarDocument(Document):
    description = fields.TextField(
        analyzer=html_strip,
        fields={"raw": fields.KeywordField()},
    )
```

## Available fields

Every field takes `attr=None` as its first argument and forwards any remaining keyword arguments to
the underlying OpenSearch field.

**Simple fields**

`BooleanField`, `ByteField`, `CompletionField`, `DateField`, `DoubleField`, `FileField`,
`FloatField`, `GeoPointField`, `GeoShapeField`, `IntegerField`, `IpField`, `KeywordField`,
`LongField`, `ScaledFloatField`, `SearchAsYouTypeField`, `ShortField`, `TextField`, `TimeField`

Two behave specially:

- `FileField` indexes a `FileField`/`ImageField` as its `.url`, or `""` when no file is set —
  never the `FieldFile` object.
- `TimeField` is a `KeywordField` that serialises `datetime.time` values with `.isoformat()`.
  OpenSearch has no native time-of-day type.

**Range fields**

`IntegerRangeField`, `LongRangeField`, `FloatRangeField`, `DoubleRangeField`, `DateRangeField`,
`IpRangeField`

A range field holds an interval rather than a point, and its value is a mapping of range bounds:

```python
@registry.register_document
class SubscriptionDocument(Document):
    active_period = fields.DateRangeField(attr="active_period")
    price_bracket = fields.DoubleRangeField()
```

The attribute must yield something like `{"gte": "2026-01-01", "lt": "2027-01-01"}`. No Django model
field maps to a range type automatically — `django.contrib.postgres` range fields are not assumed,
since the package is not a dependency here — so declare these explicitly rather than naming them in
`Django.fields`.

**Vector and relevance fields**

`KnnVectorField(dimension, attr=None, **kwargs)` holds a dense vector for k-NN search. `dimension`
is required and fixes the length of every vector stored in the field:

```python
embedding = fields.KnnVectorField(dimension=384, attr="embedding")
```

:::{important}
An index containing a `KnnVectorField` must be created with k-NN enabled, or OpenSearch rejects the
mapping outright:

```python
article_index = Index("articles")
article_index.settings(number_of_shards=1, knn=True)
```
:::

`RankFeatureField` stores a single numeric relevance boost, and `RankFeaturesField` a mapping of
names to numeric boosts, for use with the `rank_feature` query.

**Complex fields**

`ObjectField(properties, attr=None, **kwargs)` and `NestedField(properties, attr=None, **kwargs)`,
where `properties` maps field names to field instances. See
[Relationships](#relationships) below.

**`ListField(field)`**

A wrapper, not a field class. It makes the wrapped field iterate its value, for indexing a
to-many relationship as a flat list:

```python
tags = fields.ListField(fields.KeywordField(attr="tag_names"))
```

:::{warning}
An exception raised inside a property or method that a field reads is not suppressed. If `attr`
points at `Car.display_name` and that property raises, indexing fails with that error rather than
writing the field as `null`. Only a genuinely absent attribute yields `null`, and only when the
field is not `required`.
:::

## How Django fields are mapped

When you name a field in `Django.fields`, its OpenSearch type comes from this table:

| Django field | Indexed as |
| --- | --- |
| `AutoField`, `IntegerField`, `PositiveIntegerField` | `IntegerField` |
| `BigAutoField`, `BigIntegerField`, `PositiveBigIntegerField` | `LongField` |
| `SmallIntegerField`, `PositiveSmallIntegerField` | `ShortField` |
| `BooleanField`, `NullBooleanField` | `BooleanField` |
| `CharField`, `EmailField`, `TextField`, `URLField` | `TextField` |
| `SlugField`, `FilePathField`, `UUIDField` | `KeywordField` |
| `DateField`, `DateTimeField` | `DateField` |
| `TimeField` | `TimeField` |
| `DecimalField`, `FloatField` | `DoubleField` |
| `FileField`, `ImageField` | `FileField` |

A model field with no entry here raises `ModelFieldNotMappedError` at registration.

:::{note}
`DateField` and `DateTimeField` both become an OpenSearch `date`, which has no date-only variant. A
Django `DateField` therefore round-trips back out of the index as a **naive datetime at midnight**,
not a `date`.
:::

### Custom mappings

To map a field type the table does not cover, override `get_model_field_class_to_field_class()`.
Custom field classes must inherit `OSField`:

```python
from django_opensearch_models.fields import OSField
from opensearchpy import Keyword


class MyCustomField(OSField, Keyword):
    pass


class MyDocument(Document):
    @classmethod
    def get_model_field_class_to_field_class(cls):
        mapping = super().get_model_field_class_to_field_class()
        mapping[MyCustomDjangoField] = MyCustomField
        return mapping
```

## Relationships

Given a `Car` with a `ForeignKey` to `Manufacturer` and a reverse relation from `Ad`:

```python
# models.py


class Manufacturer(models.Model):
    name = models.CharField(max_length=255)
    country_code = models.CharField(max_length=2)


class Car(models.Model):
    name = models.CharField(max_length=255)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)


class Ad(models.Model):
    title = models.CharField(max_length=255)
    car = models.ForeignKey(Car, related_name="ads", on_delete=models.CASCADE)
```

embed them with `ObjectField` for a single related object and `NestedField` for a collection:

```python
# documents.py


@registry.register_document
class CarDocument(Document):
    manufacturer = fields.ObjectField(
        properties={
            "name": fields.TextField(),
            "country_code": fields.TextField(),
        }
    )
    ads = fields.NestedField(
        properties={
            "title": fields.TextField(),
            "pk": fields.IntegerField(),
        }
    )

    class Index:
        name = "cars"

    class Django:
        model = Car
        fields = ["name"]
        related_models = [Manufacturer, Ad]

    def get_queryset(self):
        # One query instead of one per car.
        return super().get_queryset().select_related("manufacturer")

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Manufacturer):
            return related_instance.car_set.all()
        if isinstance(related_instance, Ad):
            return related_instance.car
        return None
```

:::{important}
`related_models` and `get_instances_from_related()` are what keep embedded data fresh. Without them
the copy of a manufacturer's name inside every car document is written once at index time and never
updated again — renaming the manufacturer leaves every car wrong until the next full rebuild.
:::

### `ObjectField` or `NestedField`?

That choice is OpenSearch's, not this library's. `object` flattens sub-fields, so a query cannot
require that two of them match within the *same* sub-document; `nested` keeps them as separate
indexed documents and can. Nested comes at a cost in index size and query complexity. The
[OpenSearch field type documentation](https://docs.opensearch.org/latest/field-types/) covers the
trade-off.

## Analyzers

Analyzers come from `opensearch-py` and are used exactly as they are there:

```python
from opensearchpy import analyzer

html_strip = analyzer(
    "html_strip",
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"],
)


@registry.register_document
class CarDocument(Document):
    description = fields.TextField(
        analyzer=html_strip,
        fields={"raw": fields.KeywordField()},
    )
```

Changing an analyzer changes the mapping, and OpenSearch will not alter the mapping of an existing
index. Rebuild after any such change:

```console
$ ./manage.py search_index --rebuild --models myapp.Car
```
