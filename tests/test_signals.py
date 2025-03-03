from unittest import TestCase
from unittest.mock import Mock, patch

from django_opensearch_models.documents import DocType
from django_opensearch_models.registries import registry
from django_opensearch_models.signals import post_index

from .models import Car


class PostIndexSignalTestCase(TestCase):
    @patch("django_opensearch_models.documents.DocType._get_actions")
    @patch("django_opensearch_models.documents.bulk")
    def test_post_index_signal_sent(self, bulk, get_actions):
        @registry.register_document
        class CarDocument(DocType):
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
