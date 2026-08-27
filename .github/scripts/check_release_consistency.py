#!/usr/bin/env python3
"""
Assert that everything which records the project version agrees.

The version is recorded in more than one place and those places can drift.
pyproject.toml, __init__.py and the changelog must agree, and a tag must match
what they say, or a consumer pinning "the released version" gets something other
than what the artifact claims to be.

Run without --tag on every pull request: checks that the declared version is
internally consistent and that the changelog has somewhere to record changes.
Run with --tag on a tag push: additionally checks that the tag matches the
declared version and that the changelog entry for it has been dated, so a
release cannot be cut straight from an [Unreleased] section.

Exits 0 when everything agrees, 1 otherwise, printing GitHub Actions error
annotations.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
INIT = ROOT / "src" / "django_opensearch_models" / "__init__.py"
CHANGELOG = ROOT / "CHANGELOG.md"

# Matches `__version__ = "1.2.3"`. Once __init__.py derives the version from
# installed metadata instead, there is nothing to compare and the check is
# skipped -- that is the desired end state, not a failure.
LITERAL_VERSION = re.compile(r'^__version__\s*=\s*"([^"]+)"', re.MULTILINE)
DERIVES_FROM_METADATA = 'version("django-opensearch-models")'


def check(*, tag: str | None) -> list[str]:
    errors: list[str] = []

    version = tomllib.loads(PYPROJECT.read_text())["project"]["version"]

    init_source = INIT.read_text()
    if DERIVES_FROM_METADATA not in init_source:
        match = LITERAL_VERSION.search(init_source)
        if match is None:
            errors.append(f"{INIT.name} defines neither __version__ nor a metadata lookup")
        elif match.group(1) != version:
            errors.append(f"{INIT.name} __version__ is {match.group(1)!r} but project.version is {version!r}")

    if not CHANGELOG.exists():
        # A missing changelog is not worth failing an ordinary pull request over,
        # but a tag push must never pass unverified.
        if tag is not None:
            errors.append(f"cannot verify tag {tag!r}: {CHANGELOG.name} does not exist yet")
    else:
        changelog = CHANGELOG.read_text()
        if tag is None:
            if "## [Unreleased]" not in changelog:
                errors.append(f"{CHANGELOG.name} has no '## [Unreleased]' section to record changes in")
        elif not re.search(rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}", changelog, re.MULTILINE):
            errors.append(
                f"{CHANGELOG.name} has no dated '## [{version}] - YYYY-MM-DD' section; "
                f"is {version} still under [Unreleased]?"
            )

    if tag is not None and tag != version:
        errors.append(f"git tag is {tag!r} but project.version is {version!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default=None, help="The git tag being released, e.g. 1.1.0")
    args = parser.parse_args()

    errors = check(tag=args.tag)
    for error in errors:
        sys.stderr.write(f"::error::{error}\n")
    if not errors:
        sys.stderr.write("version metadata is consistent\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
