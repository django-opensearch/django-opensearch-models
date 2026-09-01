# Every change starts with a failing test

**Write the test first, watch it fail for the right reason, then write the code that passes it.**

Red, green. No production line is written before a test that demands it exists.

This covers bug fixes, new field classes, new settings, new command flags and changes to existing
behaviour. It does not cover pure documentation edits, or a rename that no test can distinguish.

**Why:** a test written after the fix only proves the code does what it already does. It never had
the chance to fail, so nothing establishes that it would catch the bug coming back. This repo's
worst defects have all been silent — a field that indexes as `None`, a rebuild that leaves an
orphaned index, a setting the code never reads. None of them raise; all of them pass a suite that
was written to agree with the implementation. A test that has failed once, for the reason you
predicted, is the only kind that holds a regression out.

**How to apply:**

1. **Red.** Write the test. Run it. Read the failure and confirm it is the failure you expected —
   the assertion you care about, not an import error, a typo, or a fixture that was never set up.
   A test that fails for the wrong reason has told you nothing.
2. **Green.** Write the smallest change that makes it pass. Run the test again.
3. Only then tidy, extend or generalise, re-running as you go.

The red step is the one that gets skipped, and it is the one carrying the value. If you find
yourself with a passing new test you never saw fail, break the production code deliberately and
confirm the test notices — then put it back.

When a bug is reported, the test reproduces the *reported symptom* before anything else:

- Not: assert that `object.__setattr__` was used.
- But: assert that `to_dict()` on a document built with `related_instance_to_ignore` does not
  contain a Django model instance.

The first restates the fix and passes for any implementation of it. The second states the bug, and
would have failed before the fix on any implementation.

**Server-dependent tests:** unit tests must not need a cluster. Anything that does belongs in
`tests/test_integration.py` — see the `run-tests` skill, including the `OPENSEARCH_REQUIRED` trap
where a skipped integration suite still reports green.
