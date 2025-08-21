import argparse
import os
import sys
from pathlib import Path

from celery import Celery

try:
    from django.conf import settings
    from django.test.utils import get_runner

    def get_settings(signal_processor):
        opensearch_default_settings = {
            "hosts": os.environ.get("OPENSEARCH_URL", "http://127.0.0.1:9200"),
            "basic_auth": (os.environ.get("OPENSEARCH_USERNAME"), os.environ.get("OPENSEARCH_PASSWORD")),
        }

        PROCESSOR_CLASSES = {
            "realtime": "django_opensearch_models.signals.RealTimeSignalProcessor",
            "celery": "django_opensearch_models.signals.CelerySignalProcessor",
        }

        signal_processor = PROCESSOR_CLASSES[signal_processor]

        settings.configure(
            DEBUG=True,
            USE_TZ=True,
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": Path(__file__).parent / "db.sqlite3",
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
            MIDDLEWARE_CLASSES=(),
            OPENSEARCH={"default": opensearch_default_settings},
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            CELERY_BROKER_URL="memory://localhost/",
            CELERY_TASK_ALWAYS_EAGER=True,
            CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
            OPENSEARCH_SIGNAL_PROCESSOR=signal_processor,
        )

        try:
            import django  # noqa: PLC0415

            setup = django.setup
        except AttributeError:
            pass
        else:
            setup()

        app = Celery()
        app.config_from_object("django.conf:settings", namespace="CELERY")
        app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
        return settings

except ImportError as e:
    import traceback

    traceback.print_exc()
    msg = "To fix this error, run: pip install -r requirements_test.txt"
    raise ImportError(msg) from e


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--opensearch",
        nargs="?",
        metavar="localhost:9200",
        const="localhost:9200",
        help="To run integration test against an OpenSearch server",
    )
    parser.add_argument(
        "--signal-processor",
        nargs="?",
        default="realtime",
        choices=("realtime", "celery"),
        help="Defines which signal backend to choose",
    )
    parser.add_argument("--opensearch-username", nargs="?", help="Username for OpenSearch user")
    parser.add_argument("--opensearch-password", nargs="?", help="Password for OpenSearch user")
    return parser


def run_tests(*test_args):
    args, test_args = make_parser().parse_known_args(test_args)
    if args.opensearch:
        os.environ.setdefault("OPENSEARCH_URL", "http://127.0.0.1:9200")

        username = args.opensearch_username or "opensearch"
        password = args.opensearch_password or "changeme"
        os.environ.setdefault("OPENSEARCH_USERNAME", username)
        os.environ.setdefault("OPENSEARCH_PASSWORD", password)

    if not test_args:
        test_args = ["tests"]

    signal_processor = args.signal_processor

    settings = get_settings(signal_processor)
    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    failures = test_runner.run_tests(test_args)

    if failures:
        sys.exit(bool(failures))


if __name__ == "__main__":
    run_tests(*sys.argv[1:])
