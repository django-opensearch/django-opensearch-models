# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases are published to PyPI and are also consumable by git tag. Tags are unprefixed (`1.1.0`, not
`v1.1.0`), and a tag push is refused unless `project.version`,
`django_opensearch_models.__version__` and a dated section here all agree — see
`.github/scripts/check_release_consistency.py`.

## [Unreleased]

### Added

- **Vector and relevance fields.** `KnnVectorField` maps a dense vector for k-NN search and takes a
  required `dimension`; the index holding one must be created with the `knn` setting enabled.
  `RankFeatureField` and `RankFeaturesField` map single and multiple numeric relevance boosts.

- **Python 3.15 support.** Added to the supported matrix, the tox environments, the CI legs and the
  classifiers. The suite runs on it under every supported Django version.

- **Range fields.** `IntegerRangeField`, `LongRangeField`, `FloatRangeField`, `DoubleRangeField`,
  `DateRangeField` and `IpRangeField`. No Django model field maps to a range type automatically, so
  these are declared explicitly rather than named in `Django.fields`.

### Changed

- An exception raised inside a property or method that a document field reads now propagates instead
  of being recorded as a missing value. A `TypeError` escaping a getter was previously
  indistinguishable from an absent attribute, so the field was indexed as `null` and nothing was
  reported.

- `queryset_pagination` now also sizes the bulk requests sent to OpenSearch on the serial path. It
  applied only under `--parallel`, leaving the serial path on the bulk helper's own default.

- The `opensearch-py` floor is raised from `>=3.0` to `>=3.1`. `KnnVectorField` needs the `KnnVector`
  DSL field, which 3.1 introduced; the 3.0 spelling `DenseVector` maps to `dense_vector`, a type
  OpenSearch has no handler for, so the field cannot work below 3.1 by any shim. Pin `1.1.0` if you
  need `opensearch-py` 3.0.

- `get_indexing_queryset()` draws its rows inside a transaction. Outside one, PostgreSQL serves the
  server-side cursor behind `iterator()` as `WITH HOLD` and materialises the entire result set to
  temporary storage before the first row is returned.

### Fixed

- `Document.to_dict()` no longer emits the internal `_related_instance_to_ignore` attribute, which
  serialized a Django model instance into the document body for any document built to skip a related
  object. Indexing was unaffected, as it goes through `prepare()`.

- A `--rebuild --use-alias` run that fails while creating or populating the new index now deletes it
  before re-raising. Nothing references that index until the alias is moved onto it and its
  timestamped name is never derived again, so failures otherwise accumulated unreachable indices.

## [1.1.0] - 2026-08-27

The first published release of django-opensearch-models.

### Added

- **Declarative documents.** A `Document` subclass pairs a Django model with an OpenSearch index.
  The `Index` inner class describes the OpenSearch side — name, shards, replicas, analyzers — and
  the `Django` inner class describes which model feeds it, via `model`, `fields`, `related_models`,
  `ignore_signals`, `auto_refresh` and `queryset_pagination`. Index mappings are derived from the
  Django field types.

- **Automatic synchronisation.** Model writes reach the index through Django's `post_save`,
  `post_delete`, `pre_delete` and `m2m_changed` signals. `RealTimeSignalProcessor` indexes inline;
  `CelerySignalProcessor` hands the work to a background task, deferring dispatch to
  `transaction.on_commit()` inside an atomic block so a worker cannot read a row before it commits.

- **Related-model tracking.** `related_models` plus `get_instances_from_related()` re-index the
  documents that embed a related object when that object changes, so denormalised copies do not go
  stale.

- **Field types.** `BooleanField`, `ByteField`, `CompletionField`, `DateField`, `DoubleField`,
  `FileField`, `FloatField`, `GeoPointField`, `GeoShapeField`, `IntegerField`, `IpField`,
  `KeywordField`, `LongField`, `ScaledFloatField`, `SearchAsYouTypeField`, `ShortField`,
  `TextField` and `TimeField`, plus `ObjectField` and `NestedField` for relationships and a
  `ListField` wrapper. Custom types subclass `OSField`; the Django-to-OpenSearch mapping table is
  overridable per document.

- **Document hooks.** `get_queryset()`, `should_index_object()`, `generate_id()`,
  `get_instances_from_related()` and `prepare_<field>()` control what is indexed and how.

- **Search integration.** `Document.search()` returns an `opensearch-py` search object with the full
  query DSL. `.to_queryset()` converts a response back into a Django queryset, preserving the search
  ordering by default.

- **`search_index` management command.** `--create`, `--populate`, `--delete` and `--rebuild`,
  scoped with `--models`, plus `--parallel`/`--no-parallel`, `--refresh`, `--no-count`, and
  `--use-alias`/`--use-alias-keep-index` for rebuilding behind an alias with no search downtime.

- **`post_index` signal**, sent after a bulk indexing operation completes.

- **Test helpers.** `django_opensearch_models.test` ships `OSTestCase`, which creates and tears down
  suffixed indices around each test, and `is_os_online()`.

- **Settings.** `OPENSEARCH` for connections, plus `OPENSEARCH_AUTOSYNC`,
  `OPENSEARCH_SIGNAL_PROCESSOR`, `OPENSEARCH_AUTO_REFRESH`, `OPENSEARCH_INDEX_SETTINGS` and
  `OPENSEARCH_PARALLEL`.

- **Supported versions.** Python 3.12–3.14, Django 5.2/6.0/6.1, `opensearch-py>=3.0,<4`, and
  OpenSearch server 2.19 and 3.8. Every combination is exercised nightly against a real cluster
  under both signal processors.

- **Distribution.** Published to PyPI via trusted publishing, with build provenance attestations
  attached to each GitHub release. The git tag remains a valid way to pin the package.

- **Documentation.** A Sphinx site at
  [django-opensearch-models.readthedocs.io](https://django-opensearch-models.readthedocs.io/en/latest/),
  written in MyST Markdown and themed with furo, covering the quickstart, documents, fields,
  indices, settings, the management command and contributing.

### Known limitations

- `OPENSEARCH_INDEX_SETTINGS` is applied after each document's own `Index.settings`, and the two are
  merged with the later write winning — so a key set project-wide overrides the same key on an
  individual document, which is the opposite of what "default" usually implies.

- Queryset-level writes emit no per-instance signals and therefore never reach the index:
  `QuerySet.update()`, `QuerySet.delete()`, `bulk_create()`, `bulk_update()` and raw SQL. Re-index
  explicitly afterwards.

- `RealTimeSignalProcessor` indexes unnormalised in-memory field values while `CelerySignalProcessor`
  re-reads the row, so the two can disagree for a field Django would coerce on save.

- `OSTestCase` mutates the global document registry and is not safe to run concurrently against a
  single cluster.

- The `post_index` signal is not sent when indexing runs in parallel, because `parallel_bulk()` has
  no single completion point to fire it from.
