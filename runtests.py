"""
Standalone test runner for django-opensearch-models.

Usage::

    python runtests.py                                  # unit tests only
    python runtests.py --opensearch                     # + integration tests
    python runtests.py --signal-processor celery        # exercise the Celery backend
    python runtests.py tests.test_fields                # a single module
"""

import argparse
import os
import sys

from django.conf import settings
from django.test.utils import get_runner

PROCESSOR_CLASSES = {
    "realtime": "django_opensearch_models.signals.RealTimeSignalProcessor",
    "celery": "django_opensearch_models.signals.CelerySignalProcessor",
}

DEFAULT_OPENSEARCH_URL = "http://127.0.0.1:9200"


def _truthy(value):
    return str(value).lower() in {"1", "true", "yes", "on"}


def opensearch_connection_settings():
    """
    Build the ``OPENSEARCH['default']`` dict from the environment.

    opensearch-py spells the credentials kwarg ``http_auth``. ``basic_auth`` is
    not a keyword it accepts, and unknown kwargs are swallowed silently by the
    transport, so getting the name wrong yields an unauthenticated client and
    every integration test skips itself via ``is_os_online()``. The key is
    omitted entirely when no credentials are set, because ``(None, None)`` blows
    up in the transport's auth header builder.
    """
    url = os.environ.get("OPENSEARCH_URL", DEFAULT_OPENSEARCH_URL)
    connection = {"hosts": url}

    username = os.environ.get("OPENSEARCH_USERNAME")
    password = os.environ.get("OPENSEARCH_PASSWORD")
    if username and password:
        connection["http_auth"] = (username, password)

    if url.startswith("https://"):
        connection["use_ssl"] = True
        connection["verify_certs"] = _truthy(os.environ.get("OPENSEARCH_VERIFY_CERTS", "1"))
        connection["ssl_show_warn"] = connection["verify_certs"]

    return connection


def configure(signal_processor):
    """Configure Django settings for the given signal processor."""
    settings.configure(
        DEBUG=True,
        USE_TZ=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sites",
            "django_opensearch_models",
            "tests",
        ],
        SITE_ID=1,
        MIDDLEWARE=[],
        OPENSEARCH={"default": opensearch_connection_settings()},
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        CELERY_BROKER_URL="memory://localhost/",
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        OPENSEARCH_SIGNAL_PROCESSOR=PROCESSOR_CLASSES[signal_processor],
    )

    import django  # ruff: ignore[import-outside-top-level]

    django.setup()

    if signal_processor == "celery":
        # celery is an optional extra, so it must not be imported unless the
        # Celery signal processor is the one under test.
        from celery import Celery  # ruff: ignore[import-outside-top-level]

        app = Celery()
        app.config_from_object("django.conf:settings", namespace="CELERY")
        app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

    return settings


def check_cluster():
    """
    Report the cluster we are pointed at, and fail loudly on a mismatch.

    The integration tests are guarded by ``unittest.skipUnless(is_os_online())``,
    evaluated at import time. Without this check, a misconfigured or unreachable
    cluster produces a fully green run that executed zero integration tests. Set
    ``OPENSEARCH_REQUIRED=1`` to turn that silent skip into a hard failure, and
    ``OPENSEARCH_SERVER`` to assert which server version answered.
    """
    from opensearchpy import connections  # ruff: ignore[import-outside-top-level]

    required = _truthy(os.environ.get("OPENSEARCH_REQUIRED", "0"))
    expected = os.environ.get("OPENSEARCH_SERVER")
    url = os.environ.get("OPENSEARCH_URL", DEFAULT_OPENSEARCH_URL)

    try:
        info = connections.get_connection("default").info()
    except Exception as exc:
        if required:
            msg = f"OPENSEARCH_REQUIRED is set but the cluster at {url} is unreachable: {exc}"
            raise SystemExit(msg) from exc
        sys.stderr.write(f"OpenSearch offline, integration tests will be skipped: {exc}\n")
        return

    actual = info["version"]["number"]
    distribution = info["version"].get("distribution", "opensearch")
    sys.stderr.write(f"Connected to {distribution} {actual} at {url}\n")

    if expected and actual != expected:
        msg = f"Expected OpenSearch {expected} but the cluster at {url} reports {actual}"
        raise SystemExit(msg)


def make_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--opensearch",
        nargs="?",
        metavar="localhost:9200",
        const="localhost:9200",
        help="Run the integration tests against an OpenSearch server",
    )
    parser.add_argument(
        "--signal-processor",
        nargs="?",
        default="realtime",
        choices=tuple(PROCESSOR_CLASSES),
        help="Which signal backend to exercise",
    )
    parser.add_argument("--opensearch-username", nargs="?", help="Username for OpenSearch")
    parser.add_argument("--opensearch-password", nargs="?", help="Password for OpenSearch")
    parser.add_argument(
        "--require-opensearch",
        action="store_true",
        help="Fail instead of skipping when the cluster is unreachable",
    )
    return parser


def run_tests(*argv):
    args, test_args = make_parser().parse_known_args(argv)

    if args.opensearch:
        os.environ.setdefault("OPENSEARCH_URL", DEFAULT_OPENSEARCH_URL)
    if args.opensearch_username:
        os.environ["OPENSEARCH_USERNAME"] = args.opensearch_username
    if args.opensearch_password:
        os.environ["OPENSEARCH_PASSWORD"] = args.opensearch_password
    if args.require_opensearch:
        os.environ["OPENSEARCH_REQUIRED"] = "1"

    configured = configure(args.signal_processor)
    check_cluster()

    runner = get_runner(configured)()
    failures = runner.run_tests(test_args or ["tests"])
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run_tests(*sys.argv[1:]))
