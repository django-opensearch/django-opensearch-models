import re

from django.test.utils import captured_stderr
from opensearchpy import connections

from django_opensearch_models.registries import registry


def is_os_online(connection_alias="default"):
    with captured_stderr():
        es = connections.get_connection(connection_alias)
        return es.ping()


class OSTestCase:
    _index_suffix = "_ded_test"

    def setUp(self):
        for doc in registry.get_documents():
            doc._index._name += self._index_suffix

        for index in registry.get_indices():
            index._name += self._index_suffix
            index.delete(ignore=[404, 400])
            index.create()

        super().setUp()

    def tearDown(self):
        pattern = re.compile(self._index_suffix + "$")

        for index in registry.get_indices():
            index.delete(ignore=[404, 400])
            index._name = pattern.sub("", index._name)

        for doc in registry.get_documents():
            doc._index._name = pattern.sub("", doc._index._name)

        super().tearDown()
