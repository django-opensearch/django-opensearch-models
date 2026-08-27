from unittest import TestCase, skipIf
from unittest.mock import Mock, patch

from django.contrib.contenttypes.models import ContentType

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
