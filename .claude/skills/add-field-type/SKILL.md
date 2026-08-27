---
name: add-field-type
description: Add a new field type to django-opensearch-models - the class in fields.py plus the four other places that must be updated together, or the field will be silently unusable or undocumented. Use when asked to add, expose or wrap an opensearch-py field type.
---

# Adding a field type

A field is not done when the class exists. Five places must change together, and three of them are
hand-maintained lists that drift easily — `ScaledFloatField`, `SearchAsYouTypeField` and
`LongField` all exist in the code but are missing from the documented field list.

## 1. `src/django_opensearch_models/fields.py`

Import the opensearch-py base at the top, then declare the class. Almost every field is a two-base
mixin with no body:

```python
class KeywordField(OSField, Keyword):
    pass
```

`OSField` **must come first** — it supplies `get_value_from_instance`, which resolves the value off
the Django model instance. Reversing the bases silently breaks value resolution.

Two exceptions to the pattern:

- `NestedField(Nested, ObjectField)` reverses the order deliberately, because `ObjectField` already
  carries `OSField`.
- A field needing to transform the Python value overrides `get_value_from_instance` rather than
  touching serialization — see `TimeField` (`.isoformat()`) and `FileFieldMixin` (`FieldFile` →
  `.url`).

## 2. `src/django_opensearch_models/__init__.py`

Two edits, both required:

- add the name to the `from .fields import (...)` block, and
- add it to `__all__`, which is a hand-maintained sorted list.

Missing the `__all__` entry means the field is importable but not part of the public surface, and it
will not appear in `from django_opensearch_models import *`.

## 3. `docs/source/fields.rst`

Add it to the "Available Fields" list under Simple or Complex Fields, matching the existing
signature style. This list is a third hand-maintained copy of the same set — it is where the drift
shows up.

## 4. `tests/test_fields.py`

One `TestCase` per field class, following the existing ones. At minimum assert that
`get_value_from_instance` returns what you expect for a populated value, an empty value and `None`.
If the field transforms the value, that transformation *is* the test.

## 5. The model-field mapping — only if applicable

`documents.py` has `model_field_class_to_field_class`, used by `Django.fields = [...]` to pick a
document field automatically from a Django model field. Add an entry **only** if there is an
unambiguous Django field that should map to your new type. `to_field()` does an exact
`model_field.__class__` lookup, so subclasses do not inherit a mapping.

Leave it alone when the right mapping is arguable — `JSONField` is deliberately unmapped for this
reason. An explicit `ModelFieldNotMappedError` is better than a wrong guess.

## Verify

```bash
uv run python runtests.py tests.test_fields          # no server needed
uv run --frozen --no-default-groups --group tox tox run -e lint
uv run python -c "import django_opensearch_models as m; print('YourField' in m.__all__)"
```

Then a real round-trip against a container, because a mapping that OpenSearch rejects only fails at
`index.create()`. See the `run-tests` skill.

## Out of scope unless asked

Vector / k-NN field support is a known gap with no ticket yet. It needs a `KnnVectorField` wrapper —
note opensearch-py 3.1 renamed the DSL field `DenseVector` to `KnnVector` — plus index-level `knn`
settings documentation. Do not add it as a side effect of another change.
