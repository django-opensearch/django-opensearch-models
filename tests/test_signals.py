from unittest import TestCase, skipIf
from unittest.mock import Mock, patch

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.test import TestCase as DjangoTestCase
from django.test import TransactionTestCase
from opensearchpy.helpers.errors import BulkIndexError

from django_opensearch_models.documents import Document
from django_opensearch_models.registries import registry
from django_opensearch_models.signals import post_index

try:
    from django_opensearch_models.signals import CelerySignalProcessor
except ImportError:  # celery is an optional extra
    CelerySignalProcessor = None

from .models import Car, Category


class PostIndexSignalTestCase(TestCase):
    @patch("django_opensearch_models.documents.Document._get_actions")
    @patch("django_opensearch_models.documents.bulk")
    def test_post_index_signal_sent(self, bulk, get_actions):
        @registry.register_document
        class CarDocument(Document):
            class Django:
                fields = ["name"]
                model = Car

        bulk.return_value = (1, [])

        # register a mock signal receiver
        mock_receiver = Mock()
        post_index.connect(mock_receiver)

        doc = CarDocument()
        car = Car(pk=51, name="Type 57")
        doc.update(car)

        bulk.assert_called_once()

        mock_receiver.assert_called_once_with(
            signal=post_index, sender=CarDocument, instance=doc, actions=get_actions(), response=(1, [])
        )


@skipIf(CelerySignalProcessor is None, "celery is not installed")
class CelerySignalProcessorTestCase(TestCase):
    """Guard the predicate that decides whether a change is worth a Celery task."""

    def setUp(self):
        # Only the predicate is under test, so skip __init__ and its signal wiring.
        self.processor = CelerySignalProcessor.__new__(CelerySignalProcessor)

    def test_model_with_its_own_document_is_indexed(self):
        self.assertTrue(self.processor.is_instance_indexed(Car(pk=1, name="Type 57")))

    def test_related_only_model_is_indexed(self):
        """
        A model that only appears in another document's ``related_models``.

        Category has no document of its own, but CarDocument embeds it, so a
        change to a Category has to reindex the affected cars. Gating on
        ``registry._models`` alone skipped these instances entirely and the
        embedded data went stale -- see is_instance_indexed().
        """
        self.assertIn(Category, registry._related_models)
        self.assertNotIn(Category, registry._models)
        self.assertTrue(self.processor.is_instance_indexed(Category(pk=1, title="Sedans")))

    def test_unrelated_model_is_not_indexed(self):
        self.assertFalse(self.processor.is_instance_indexed(ContentType(pk=1)))


@skipIf(CelerySignalProcessor is None, "celery is not installed")
class CelerySignalProcessorDeleteTestCase(TestCase):
    """
    `delete` must remove the document for a row that is already gone.

    By the time a worker runs the task the row has been deleted, so `deserialize_instance` can only
    ever return `None` for it. `delete` must therefore reach `registry.delete` without consulting the
    database -- anything that requires a live row here drops the document from the index silently.
    """

    @patch.object(registry, "delete")
    def test_deletes_a_pk_with_no_matching_row(self, mock_delete):
        CelerySignalProcessor.delete("tests", "Car", 999999)

        mock_delete.assert_called_once()
        (deleted_instance,), _ = mock_delete.call_args
        self.assertIsInstance(deleted_instance, Car)
        self.assertEqual(deleted_instance.pk, 999999)

    @patch.object(registry, "delete")
    def test_returns_quietly_for_an_unknown_model(self, mock_delete):
        CelerySignalProcessor.delete("tests", "NoSuchModel", 1)

        mock_delete.assert_not_called()

    @patch.object(registry, "delete")
    def test_swallows_a_404_bulk_error(self, mock_delete):
        # Celery's at-least-once delivery can dispatch the same delete twice; the second attempt 404s.
        mock_delete.side_effect = BulkIndexError("1 document(s) failed to delete", [{"delete": {"status": 404}}])

        CelerySignalProcessor.delete("tests", "Car", 1)  # must not raise

    @patch.object(registry, "delete")
    def test_reraises_a_non_404_bulk_error(self, mock_delete):
        mock_delete.side_effect = BulkIndexError("1 document(s) failed to delete", [{"delete": {"status": 500}}])

        with self.assertRaises(BulkIndexError):
            CelerySignalProcessor.delete("tests", "Car", 1)


def register_car_document():
    """Register a throwaway `CarDocument` so `Car` is seen as indexed by `is_instance_indexed`."""

    @registry.register_document
    class CarDocument(Document):
        class Index:
            # A distinct name so this throwaway document doesn't share index state with any other
            # Document subclass in the suite (e.g. tests/test_documents.py's own "car_index").
            name = "test_signals_car_index"

        class Django:
            fields = ["name"]
            model = Car


@skipIf(CelerySignalProcessor is None, "celery is not installed")
class CelerySignalProcessorHandleSaveDeferredTestCase(DjangoTestCase):
    """
    Inside a transaction, `handle_save` must not enqueue a task until that transaction commits.

    `post_save` fires before an enclosing transaction commits. Enqueuing immediately would let a
    worker read the row on another connection before the transaction makes it visible there, and
    index whatever stale or absent state it finds.

    Calls `handle_save` directly on an isolated instance rather than going through a real `post_save` signal:
    CI runs the suite under both signal processors, and only one of them is `CelerySignalProcessor`, so
    relying on whichever one is live would make this pass under one and fail under the other.
    """

    def setUp(self):
        register_car_document()
        # Bypass __init__/setup(): it connects the processor to Django's live signals, which would leak
        # a second receiver into every other test in the suite.
        self.processor = CelerySignalProcessor.__new__(CelerySignalProcessor)

    @patch.object(CelerySignalProcessor, "save")
    def test_dispatch_deferred_until_transaction_commits(self, mock_save):
        car = Car(pk=1, name="Type 57")
        with self.captureOnCommitCallbacks(execute=True), transaction.atomic():
            self.processor.handle_save(Car, car)
            mock_save.delay.assert_not_called()

        mock_save.delay.assert_called_once_with("tests", "Car", 1)


@skipIf(CelerySignalProcessor is None, "celery is not installed")
class CelerySignalProcessorHandleSaveImmediateTestCase(TransactionTestCase):
    """Outside any transaction, `handle_save` enqueues the task immediately."""

    def setUp(self):
        register_car_document()
        self.processor = CelerySignalProcessor.__new__(CelerySignalProcessor)

    @patch.object(CelerySignalProcessor, "save")
    def test_dispatch_immediate_outside_an_atomic_block(self, mock_save):
        # TransactionTestCase does not wrap the test in a transaction, unlike TestCase.
        car = Car(pk=1, name="Type 57")
        self.processor.handle_save(Car, car)

        mock_save.delay.assert_called_once_with("tests", "Car", 1)
