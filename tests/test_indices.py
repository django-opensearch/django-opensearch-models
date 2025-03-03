from unittest import TestCase
from unittest.mock import patch

from django.conf import settings

from django_opensearch_models.indices import Index
from django_opensearch_models.registries import DocumentRegistry

from .fixtures import WithFixturesMixin


class IndexTestCase(WithFixturesMixin, TestCase):
    def setUp(self):
        self.registry = DocumentRegistry()

    def test_documents_add_to_register(self):
        registry = self.registry
        with patch("django_opensearch_models.indices.registry", new=registry):
            index = Index("test")
            doc_a1 = self._generate_doc_mock(self.ModelA)
            doc_a2 = self._generate_doc_mock(self.ModelA)
            index.document(doc_a1)
            docs = list(registry.get_documents())
            self.assertEqual(len(docs), 1)
            self.assertIs(docs[0], doc_a1)

            index.document(doc_a2)
            docs = registry.get_documents()
            self.assertEqual(docs, {doc_a1, doc_a2})

    def test__str__(self):
        index = Index("test")
        self.assertEqual(str(index), "test")

    def test__init__(self):
        settings.OPENSEARCH_INDEX_SETTINGS = {
            "number_of_replicas": 0,
            "number_of_shards": 2,
        }

        index = Index("test")
        self.assertEqual(
            index._settings,
            {
                "number_of_replicas": 0,
                "number_of_shards": 2,
            },
        )

        settings.OPENSEARCH_INDEX_SETTINGS = {}
