---
name: run-tests
description: Run the django-opensearch-models test suite correctly - starting a throwaway OpenSearch container, choosing a signal processor, and running one tox environment or the whole matrix. Use whenever asked to run, debug or add tests in this repo, or when a test result needs to be trusted.
---

# Running the tests

## Never use a shared cluster

The integration tests create, populate and delete indices, and `OSTestCase` mutates the global
document registry. Point them at a development cluster and they will leave debris in it and can
drive it to a red state.

Start a throwaway container on **9201**, not 9200:

```bash
docker run -d --name dosm-test-os -p 9201:9200 \
  -e discovery.type=single-node -e "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g" \
  -e DISABLE_INSTALL_DEMO_CONFIG=true -e "plugins.security.disabled=true" \
  --ulimit nofile=65536:65536 opensearchproject/opensearch:3.8.0

until curl -fsS -m 3 http://127.0.0.1:9201/_cluster/health >/dev/null 2>&1; do sleep 3; done
export OPENSEARCH_URL=http://127.0.0.1:9201 OPENSEARCH_SERVER=3.8.0 OPENSEARCH_REQUIRED=1
```

Do **not** pass `-e index.number_of_replicas=0`: index-level settings are rejected as node settings
and the container will not boot.

## Always set OPENSEARCH_REQUIRED=1

The integration tests are guarded by `unittest.skipUnless(is_os_online())`. Without
`OPENSEARCH_REQUIRED=1`, an unreachable or misconfigured cluster produces a **fully green run that
executed zero integration tests**. `OPENSEARCH_SERVER` additionally asserts which server version
answered, so a run cannot silently test the wrong one.

## Running

```bash
# Whole suite, realtime signal processor
uv run python runtests.py

# The Celery processor. CI runs both; a change that only passes one is not done.
uv run python runtests.py --signal-processor celery

# One module
uv run python runtests.py tests.test_fields

# One tox environment (runs BOTH processors)
uv run --frozen --no-default-groups --group tox tox run -e py314-dj61

# The full matrix: 3 pythons x 3 djangos, both processors
uv run --frozen --no-default-groups --group tox tox run
```

Other environments: `lint`, `build`, `docs`, `coverage`, and `lowest` (installs the declared
dependency floors rather than the lockfile).

## Run one thing at a time against the cluster

`OSTestCase` renames indices in the global registry during `setUp` and strips the suffix in
`tearDown`. Two runs sharing one cluster collide in `index.create()` and accumulate suffixes, giving
failures like `_index': 'car_index_os_test_os_test'` that look like code bugs and are not.

So: **no `tox run-parallel`**, and do not start a second run while the matrix is going. If you see
accumulated suffixes, recreate the container rather than debugging the test.

## Before believing a failure

1. Is a second run using the same cluster?
2. Is the failure also on `main`? Check with a worktree before assuming you caused it:
   ```bash
   git worktree add /tmp/wt-main main && cd /tmp/wt-main && uv sync --dev
   ```
3. Are `OPENSEARCH_URL` / `OPENSEARCH_SERVER` / `OPENSEARCH_REQUIRED` actually exported? tox only
   forwards the variables named in `pass_env`.

## Adding tests

- Unit tests must not need a server. `tests/test_commands.py` patches
  `search_index.connections.get_connection`; follow that rather than reintroducing a live dependency.
- Server-dependent tests belong in `tests/test_integration.py`, on a class deriving from
  `OSTestCase`.
- Test data must match the model field type. Assigning an aware `datetime` to a `DateField` makes the
  two signal processors disagree, because the realtime one indexes the in-memory value and the Celery
  one re-reads the row.
- A `DateField` round-trips out of OpenSearch as a **naive datetime at midnight**, not a `date`. See
  `IntegrationTestCase.as_indexed_date`.

## Cleanup

```bash
docker rm -f dosm-test-os
rm -f .coverage .coverage.* coverage.xml
```
