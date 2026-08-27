# Comments describe the present

**Never write a comment, docstring or test name that explains what the code used to do.**

No "previously", "used to", "no longer", "this was broken in X", "regression test for Y", "which is
why nobody noticed". A reader wants to know what the code does now and which constraint forces it to
be this way. What it did before is not a constraint — it is gone.

This covers comments, docstrings, workflow YAML comments, config comments and skill or rule files.
`CHANGELOG.md`, `NOTICE` and `LICENSE` are the exceptions: recording history is the entire job of
the first and a licence obligation for the other two.

**Why:** a comment describing a past state ages into a lie the moment someone reads it as current,
and it makes a maintained codebase read like an archaeological dig. It also costs a reader time to
work out that a paragraph they just read describes nothing that exists.

**How to apply:** keep the *constraint*, drop the *history*. The reason a bug was possible is
usually a fact about the system that still holds, and that fact is worth writing down.

- Not: "Regression test: `delete` used to re-read the row, which always returned `None`."
- But: "By the time a worker runs the task the row is gone, so `delete` must reach
  `registry.delete` without consulting the database."

- Not: "The `test` subpackage was stripped from the 1.0.0 artifacts by a bad exclude pattern."
- But: "Build-backend exclude patterns match a bare name at any depth, so a pattern meant for the
  top-level `tests/` directory can also strip the package's own `test/`."

Both versions explain why the code is the way it is. Only one of them still makes sense in a year.
