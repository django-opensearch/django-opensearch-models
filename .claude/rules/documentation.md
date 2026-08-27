# Documentation must track the API

**Any change to the public API updates the documentation in the same commit.**

Public API is anything a consumer of the library can touch:

- a setting name, its default, or what it does
- an option on a `Document`'s `Django` or `Index` inner class
- an overridable hook on `Document` (`get_queryset`, `should_index_object`,
  `get_instances_from_related`, `generate_id`, `prepare_<field>`, …)
- a field class, or the Django-field-to-OpenSearch-field mapping table
- a signal, or the arguments it is sent with
- a `search_index` action or flag
- the supported Python / Django / opensearch-py / OpenSearch version matrix

A change that adds, removes, renames or alters the behaviour of any of those is not finished until
the corresponding page under `docs/source/` says so. Adding a setting without its entry in
`settings.md` leaves the PR incomplete.

**Why:** documentation drifts from code silently, and drifted documentation is worse than none.
A setting name the code does not read looks identical to one it does until someone tries it — the
cluster is never contacted and the index stays empty, with no error anywhere. A support matrix that
lags the CI matrix sends people to a version that was never tested. A field reference missing
classes that exist means nobody uses them. Each of those is one small API change that skipped the
docs.

**How to apply:** invoke the `docs` skill — it covers the page layout, the README single-sourcing
rule, and how to build with warnings as errors. Verify behaviour against the source before writing
it down; do not trust an existing sentence just because it is already there.
