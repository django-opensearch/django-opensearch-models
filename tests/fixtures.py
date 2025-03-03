from unittest.mock import Mock

from django.db import models

from django_opensearch_models.documents import DocType


class WithFixturesMixin:
    class ModelA(models.Model):
        class Meta:
            app_label = "foo"

        def __str__(self):
            return self.id

    class ModelB(models.Model):
        class Meta:
            app_label = "foo"

        def __str__(self):
            return self.id

    class ModelC(models.Model):
        class Meta:
            app_label = "bar"

        def __str__(self):
            return self.id

    class ModelD(models.Model):
        def __str__(self):
            return self.id

    class ModelE(models.Model):
        def __str__(self):
            return self.id

    def _generate_doc_mock(self, _model, index=None, mock_qs=None, _ignore_signals=False, _related_models=None):
        index_ = index

        class Doc(DocType):
            class Django:
                model = _model
                related_models = _related_models if _related_models is not None else []
                ignore_signals = _ignore_signals

        if index_:
            index_.document(Doc)
            self.registry.register_document(Doc)

        Doc.update = Mock()
        if mock_qs:
            Doc.get_queryset = Mock(return_value=mock_qs)
        if _related_models:
            Doc.get_instances_from_related = Mock()

        return Doc
