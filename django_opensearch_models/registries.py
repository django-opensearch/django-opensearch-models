from collections import defaultdict
from copy import deepcopy
from itertools import chain

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from opensearchpy import AttrDict

from django_opensearch_models.exceptions import RedeclaredFieldError

from .apps import DEDConfig


class DocumentRegistry:
    """Registry of models classes to a set of Document classes."""

    def __init__(self):
        self._indices = defaultdict(set)
        self._models = defaultdict(set)
        self._related_models = defaultdict(set)

    def register(self, index, doc_class):
        """Register the model with the registry."""
        self._models[doc_class.django.model].add(doc_class)

        for related in doc_class.django.related_models:
            self._related_models[related].add(doc_class.django.model)

        for idx, docs in self._indices.items():
            if index._name == idx._name:
                docs.add(doc_class)
                return

        self._indices[index].add(doc_class)

    def register_document(self, document):
        django_meta = document.Django
        # Raise error if Django class can not be found
        if not django_meta:
            message = f"You must declare the Django class inside {document.__name__}"
            raise ImproperlyConfigured(message)

        # Keep all django related attribute in a django_attr AttrDict
        data = {"model": document.Django.model}
        django_attr = AttrDict(data)

        if not django_attr.model:
            msg = "You must specify the django model"
            raise ImproperlyConfigured(msg)

        # Add The model fields into opensearch mapping field
        model_field_names = getattr(document.Django, "fields", [])
        mapping_fields = document._doc_type.mapping.properties.properties.to_dict().keys()

        for field_name in model_field_names:
            if field_name in mapping_fields:
                msg = f"You cannot redeclare the field named '{field_name}' on {document.__name__}"
                raise RedeclaredFieldError(msg)

            django_field = django_attr.model._meta.get_field(field_name)

            field_instance = document.to_field(field_name, django_field)
            document._doc_type.mapping.field(field_name, field_instance)

        django_attr.ignore_signals = getattr(django_meta, "ignore_signals", False)
        django_attr.auto_refresh = getattr(django_meta, "auto_refresh", DEDConfig.auto_refresh_enabled())
        django_attr.related_models = getattr(django_meta, "related_models", [])
        django_attr.queryset_pagination = getattr(django_meta, "queryset_pagination", None)

        # Add django attribute in the document class with all the django attribute
        document.django = django_attr

        # Set the fields of the mappings
        fields = document._doc_type.mapping.properties.properties.to_dict()
        document._fields = fields

        # Update settings of the document index
        default_index_settings = deepcopy(DEDConfig.default_index_settings())
        document._index.settings(**default_index_settings)

        # Register the document and index class to our registry
        self.register(index=document._index, doc_class=document)

        return document

    def _get_related_doc(self, instance):
        for model in self._related_models.get(instance.__class__, []):
            for doc in self._models[model]:
                if instance.__class__ in doc.django.related_models:
                    yield doc

    def update_related(self, instance, **kwargs):
        """Update docs that have related_models."""
        if not DEDConfig.autosync_enabled():
            return

        for doc in self._get_related_doc(instance):
            doc_instance = doc()
            try:
                related = doc_instance.get_instances_from_related(instance)
            except ObjectDoesNotExist:
                related = None

            if related is not None:
                doc_instance.update(related, **kwargs)

    def delete_related(self, instance, **kwargs):
        """Remove `instance` from related models."""
        if not DEDConfig.autosync_enabled():
            return

        for doc in self._get_related_doc(instance):
            doc_instance = doc(related_instance_to_ignore=instance)
            try:
                related = doc_instance.get_instances_from_related(instance)
            except ObjectDoesNotExist:
                related = None

            if related is not None:
                doc_instance.update(related, **kwargs)

    def update(self, instance, **kwargs):
        """Update all the opensearch documents attached to this model (if their ignore_signals flag allows it)."""
        if not DEDConfig.autosync_enabled():
            return

        if instance.__class__ in self._models:
            for doc in self._models[instance.__class__]:
                if not doc.django.ignore_signals:
                    doc().update(instance, **kwargs)

    def delete(self, instance, **kwargs):
        """Delete all the opensearch documents attached to this model (if their ignore_signals flag allows it)."""
        self.update(instance, action="delete", **kwargs)

    def get_documents(self, models=None):
        """Get all documents in the registry or the documents for a list of models."""
        if models is not None:
            return set(chain.from_iterable(self._models[model] for model in models if model in self._models))
        return set(chain.from_iterable(self._indices.values()))

    def get_models(self):
        """Get all models in the registry."""
        return set(self._models.keys())

    def get_indices(self, models=None):
        """Get all indices in the registry or the indices for a list of models."""
        if models is not None:
            return {indice for indice, docs in self._indices.items() for doc in docs if doc.django.model in models}

        return set(self._indices.keys())

    def __contains__(self, model):
        """Check that model is in registry."""
        return model in self._models or model in self._related_models


registry = DocumentRegistry()
