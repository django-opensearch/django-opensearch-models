"""
Sphinx configuration.

Every value here differs from the Sphinx default; anything not set is the
default on purpose.

`uv sync --group docs` installs the project itself, so
`import django_opensearch_models` resolves without any `sys.path` manipulation.
Under this project's src layout the repository root does not contain the
package, so adding it to the path would achieve nothing anyway.
"""

from importlib.metadata import version as version_of

# -- Project information -----------------------------------------------------

project = "django-opensearch-models"
author = "django-opensearch contributors"
# The project's own copyright. Attribution required to be retained for derived
# portions lives in NOTICE, which is where it belongs -- not duplicated here.
copyright = "2026, django-opensearch contributors"

# Read from installed distribution metadata rather than written out here, so
# pyproject.toml stays the single place the version is recorded.
release = version_of("django-opensearch-models")
version = ".".join(release.split(".", 3)[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    # Renders Google- and NumPy-style docstrings, which is what the source
    # actually uses. Without it autodoc prints the raw `Args:` blocks.
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_design",
]

# Every page is Markdown, parsed by MyST. reStructuredText is deliberately not
# registered: one markup language, no "which syntax is this file" question.
source_suffix = {".md": "markdown"}

# Sphinx rejects None here and the docs env builds with -W.
language = "en"
exclude_patterns = []

# Bare `text` renders as inline code, which is what a Markdown author expects a
# backtick to do. Not "py:obj": there is no autodoc API reference for those
# references to resolve against, and it would try to resolve filenames like
# `documents.py` as Python objects.
default_role = "literal"

# -- Cross-project links -----------------------------------------------------

# The reason this project stays on Sphinx: Django and opensearch-py both publish
# an inventory, so references into them resolve to real links. Django serves its
# inventory from a non-standard path, hence the explicit second element.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": (
        "https://docs.djangoproject.com/en/stable/",
        "https://docs.djangoproject.com/en/stable/_objects/",
    ),
    "opensearchpy": ("https://opensearch-project.github.io/opensearch-py/", None),
}

# The docs tell contributors to open the live preview at 127.0.0.1:8000. That is
# an instruction, not a link to a real site, and linkcheck cannot resolve it.
linkcheck_ignore = [r"^https?://127\.0\.0\.1(:\d+)?/?"]

# -- MyST --------------------------------------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "smartquotes",
]
myst_heading_anchors = 3

# -- HTML output -------------------------------------------------------------

html_theme = "furo"
html_title = f"{project} {version}"

html_theme_options = {
    # Drives furo's "Edit this page" links. The org, repository and branch must
    # match reality or every source link 404s.
    "source_repository": "https://github.com/django-opensearch/django-opensearch-models/",
    "source_branch": "master",
    "source_directory": "docs/source/",
}

# furo ships a dark mode; without a dark pygments style the code blocks stay on
# a light background inside it.
pygments_style = "sphinx"
pygments_dark_style = "monokai"
