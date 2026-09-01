# Management commands

One command, `search_index`, does everything. It takes exactly one action and an optional set of
models to apply it to.

```console
$ ./manage.py search_index --rebuild
```

## Actions

`--create`
: Create the indices and their mappings. Fails if the index already exists. If the name is currently
  an *alias*, it prints how to free the name instead of failing.

`--populate`
: Index the model data into indices that already exist. Does not create or delete anything.

`--delete`
: Delete the indices and everything in them.

`--rebuild`
: `--delete` followed by `--create` and `--populate`. The usual choice after a mapping change.

## Scope

`--models app[.model] ...`
: Limit the action to specific apps or models. `--models myapp` covers every document in that app;
  `--models myapp.Car myapp.Ad` names them individually. An app or model that is not registered is
  an error, not a silent no-op. Without this flag the action applies to every registered document.

## Options

`-f`
: Do not prompt for confirmation. `--delete`, and `--rebuild` without `--use-alias`, otherwise stop
  and ask before destroying an index — so `-f` is required for anything non-interactive.
  `--rebuild --use-alias` does not prompt: it builds a new index alongside the live one and deletes
  nothing until the alias has moved.

`--parallel` / `--no-parallel`
: Index with `parallel_bulk()` rather than serially. Defaults to
  [`OPENSEARCH_PARALLEL`](settings.md#opensearch_parallel). Faster on large tables, but opens
  several database connections (SQLite does not cope) and suppresses the
  {ref}`post_index <post-index-signal>` signal.

`--refresh`
: Refresh the indices once population finishes, so the data is immediately searchable instead of
  waiting for OpenSearch's own refresh interval.

`--use-alias`
: Treat the document's index name as an alias, and rebuild into a fresh timestamped index that the
  alias is atomically repointed at. Searches never see a missing or half-populated index. See
  {ref}`Rebuilding without downtime <rebuilding-without-downtime>`. If creating or populating that
  new index fails, it is deleted before the error is re-raised — nothing references it, and its
  timestamped name is never derived again — so a retry starts clean rather than accumulating
  half-built indices.

`--use-alias-keep-index`
: With `--rebuild --use-alias`, keep the index the alias previously pointed at instead of deleting
  it. Cleaning those up afterwards is then your responsibility.

`--no-count`
: Skip the total-row count in the summary line. That count is a `COUNT(*)` over the whole table,
  which on a large one can take longer than the indexing.

## Recipes

Rebuild one model's index after changing its mapping:

```console
$ ./manage.py search_index --rebuild --models myapp.Car -f
```

Rebuild everything in production without a search outage:

```console
$ ./manage.py search_index --rebuild --use-alias --parallel -f
```

Re-populate without touching the mapping, for example after a bulk `QuerySet.update()` that emitted
no signals:

```console
$ ./manage.py search_index --populate --models myapp.Car --refresh
```

Start clean in development:

```console
$ ./manage.py search_index --delete -f
$ ./manage.py search_index --create
```
