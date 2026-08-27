# django-opensearch-models

[![CI](https://github.com/django-opensearch/django-opensearch-models/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/django-opensearch/django-opensearch-models/actions/workflows/ci.yml)
[![Coverage](https://raw.githubusercontent.com/django-opensearch/django-opensearch-models/python-coverage-comment-action-data/badge.svg)](https://github.com/django-opensearch/django-opensearch-models/tree/python-coverage-comment-action-data)
[![PyPI](https://img.shields.io/pypi/v/django-opensearch-models?label=pypi)](https://pypi.org/project/django-opensearch-models/)
[![Python](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2Fdjango-opensearch%2Fdjango-opensearch-models%2Fmaster%2Fpyproject.toml&query=%24.project.requires-python&label=python)](https://github.com/django-opensearch/django-opensearch-models/blob/master/pyproject.toml)
[![Docs](https://readthedocs.org/projects/django-opensearch-models/badge/?version=latest)](https://django-opensearch-models.readthedocs.io/en/latest/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://github.com/django-opensearch/django-opensearch-models/blob/master/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

<!-- overview-start -->
Index your Django models in [OpenSearch](https://opensearch.org) and keep them in sync
automatically.

You describe an index by declaring a `Document` class against a model, and the library handles the
rest: it builds the OpenSearch mapping from your Django fields, populates the index, and updates it
on every `save()` and `delete()` through Django's signal framework. Search results convert back into
real Django querysets when you need them.

**What you get**

- **Declarative documents.** A `Document` subclass maps a Django model to an OpenSearch index —
  fields, analyzers, index settings and all.
- **Automatic synchronisation.** Model changes reach the index through signals, either inline or
  handed to Celery as background tasks.
- **Related-model tracking.** Declare `related_models` and edits to a `ForeignKey` target re-index
  the documents that embed it.
- **Management commands.** Create, populate, rebuild and delete indices, with zero-downtime
  rebuilds behind an alias and optional parallel indexing.
- **Querysets from search results.** `.to_queryset()` turns a search response back into a Django
  queryset, ordered to match the search.
<!-- overview-end -->

## Requirements

<!-- requirements-start -->
| | Supported versions |
| --- | --- |
| Python | 3.12, 3.13, 3.14 |
| Django | 5.2, 6.0, 6.1 |
| [opensearch-py](https://github.com/opensearch-project/opensearch-py) | 3.x |
| OpenSearch server | 2.19, 3.8 |

Every combination in that table is exercised nightly against a real OpenSearch cluster, under both
signal processors.
<!-- requirements-end -->

## Installation

```console
$ pip install django-opensearch-models
```

## Quick start

<!-- example-start -->
Add the app and point it at your cluster:

```python
# settings.py

INSTALLED_APPS = [
    ...,
    "django_opensearch_models",
]

OPENSEARCH = {
    "default": {
        "hosts": "localhost:9200",
        "http_auth": ("username", "password"),
    },
}
```

Declare a document for the model you want to index, in your app's `documents.py`:

```python
# documents.py

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
        fields = ["name", "color", "description"]
```

Build the index:

```console
$ ./manage.py search_index --rebuild
```

From here on, saving a `Car` indexes it. Searching returns OpenSearch hits, or Django objects:

```python
hits = CarDocument.search().filter("term", color="red")

for hit in hits:
    print(hit.name, hit.description)

# ...or come back to the ORM
cars = CarDocument.search().filter("term", color="red")[:30].to_queryset()
```
<!-- example-end -->

## Documentation

Full documentation is at
**[django-opensearch-models.readthedocs.io](https://django-opensearch-models.readthedocs.io/en/latest/)**.

- [Quickstart](https://django-opensearch-models.readthedocs.io/en/latest/quickstart.html) — install, configure, index and search
- [Indices](https://django-opensearch-models.readthedocs.io/en/latest/indices.html) — index objects, aliases and the `post_index` signal
- [Fields](https://django-opensearch-models.readthedocs.io/en/latest/fields.html) — field types, relationships and custom mappings
- [Settings](https://django-opensearch-models.readthedocs.io/en/latest/settings.html) — every setting the app reads
- [Commands](https://django-opensearch-models.readthedocs.io/en/latest/commands.html) — the `search_index` management command
- [Contributing](https://django-opensearch-models.readthedocs.io/en/latest/develop.html) — running the tests and the support matrix

## Contributing

Issues and pull requests are welcome at
[github.com/django-opensearch/django-opensearch-models](https://github.com/django-opensearch/django-opensearch-models).
See the [contributing guide](https://django-opensearch-models.readthedocs.io/en/latest/develop.html)
for how to run the test suite against a throwaway OpenSearch container.

## License

Apache-2.0. See
[LICENSE](https://github.com/django-opensearch/django-opensearch-models/blob/master/LICENSE) and
[NOTICE](https://github.com/django-opensearch/django-opensearch-models/blob/master/NOTICE).
