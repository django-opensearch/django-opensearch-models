from copy import deepcopy

from opensearchpy import Index as OSIndex

from .apps import DEDConfig
from .registries import registry


class Index(OSIndex):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_index_settings = deepcopy(DEDConfig.default_index_settings())
        self.settings(**default_index_settings)

    def document(self, document):
        """Extend to register the document in the global document registry."""
        document = super().document(document)
        registry.register_document(document)
        return document

    doc_type = document

    def __str__(self):
        return self._name
