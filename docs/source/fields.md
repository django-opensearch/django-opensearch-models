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
the underlying OpenSearch field. Two of them add a required argument of their own, shown in the
tables below.

:::{warning}
`attr` resolution does not report every failure. A `TypeError` from a property or descriptor
propagates, as does anything raised by a method the field calls, so indexing fails with that error
rather than writing `null`. An `AttributeError` does not: it cannot be told apart from an absent
attribute, so it yields `null`, or `VariableLookupError` when the field is `required`. A missing
related object raises `ObjectDoesNotExist`, which always yields `null` and ignores `required`.
:::

### Simple fields

| Field | Indexed as |
| --- | --- |
| `BooleanField` | `boolean` |
| `ByteField` | `byte` |
| `CompletionField` | `completion` |
| `DateField` | `date` |
| `DoubleField` | `double` |
| `FileField` | `text` |
| `FloatField` | `float` |
| `GeoPointField` | `geo_point` |
| `GeoShapeField` | `geo_shape` |
| `IntegerField` | `integer` |
| `IpField` | `ip` |
| `KeywordField` | `keyword` |
| `LongField` | `long` |
| `ScaledFloatField(scaling_factor=...)` | `scaled_float` |
| `SearchAsYouTypeField` | `search_as_you_type` |
| `ShortField` | `short` |
| `TextField` | `text` |
| `TimeField` | `keyword` |

Three of these are more than a rename of the underlying type:

`FileField`
: Indexes a Django `FileField` or `ImageField` as its `.url`, or `""` when no file is set — never the
  `FieldFile` object.

`ScaledFloatField`
: Requires `scaling_factor`. OpenSearch stores the value as a long multiplied by that factor, so
  `scaling_factor=100` keeps two decimal places.

`TimeField`
: A `KeywordField` that serialises `datetime.time` values with `.isoformat()`. OpenSearch has no
  native time-of-day type.

### Range fields

| Field | Indexed as |
| --- | --- |
| `DateRangeField` | `date_range` |
| `DoubleRangeField` | `double_range` |
| `FloatRangeField` | `float_range` |
| `IntegerRangeField` | `integer_range` |
| `IpRangeField` | `ip_range` |
| `LongRangeField` | `long_range` |

A range field holds an interval rather than a point, so the attribute must yield a mapping of bounds
such as `{"gte": "2026-01-01", "lt": "2027-01-01"}` rather than a single value:

```python
@registry.register_document
class SubscriptionDocument(Document):
    active_period = fields.DateRangeField(attr="active_period")
    price_bracket = fields.DoubleRangeField()
```

No Django model field maps to a range type automatically, since `django.contrib.postgres` is not a
dependency here. Declare these on the document rather than naming them in `Django.fields`.

### Vector and relevance fields

| Field | Indexed as |
| --- | --- |
| `KnnVectorField(dimension=...)` | `knn_vector` |
| `RankFeatureField` | `rank_feature` |
| `RankFeaturesField` | `rank_features` |

`KnnVectorField`
: A dense vector for k-NN search. `dimension` is required and fixes the length of every vector
  stored in the field.

`RankFeatureField`
: A single numeric relevance boost, queried with `rank_feature`.

`RankFeaturesField`
: A mapping of names to numeric boosts, queried the same way — for a document carrying one boost per
  category rather than a single score.

```python
embedding = fields.KnnVectorField(dimension=384, attr="embedding")
popularity = fields.RankFeatureField()
topics = fields.RankFeaturesField()
```

:::{important}
An index containing a `KnnVectorField` must be created with k-NN enabled, or OpenSearch rejects the
mapping outright:

```python
article_index = Index("articles")
article_index.settings(number_of_shards=1, knn=True)
```
:::

### Object and nested fields

| Field | Indexed as |
| --- | --- |
| `ObjectField` | `object` |
| `NestedField` | `nested` |

Both take `properties` as a keyword argument, mapping field names to field instances. `attr` remains
the first positional argument, as it is for every other field. See [Relationships](#relationships)
for how they are used, and {ref}`ObjectField or NestedField? <object-or-nested>` for choosing between
them.

### `ListField`

A wrapper rather than a field class, so it has no mapping type of its own. It makes the wrapped field
iterate its value, for indexing a to-many relationship as a flat list:

```python
tags = fields.ListField(fields.KeywordField(attr="tag_names"))
```

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

(object-or-nested)=
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
