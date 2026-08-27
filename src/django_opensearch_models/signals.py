"""A convenient way to attach django-opensearch-models to Django's signals and cause things to index."""

from functools import partial
from http import HTTPStatus

from django.apps import apps
from django.db import connection, models, transaction
from django.dispatch import Signal
from opensearchpy.helpers.errors import BulkIndexError

from .registries import registry

# Sent after document indexing is completed
post_index = Signal()


class BaseSignalProcessor:
    """
    Base signal processor.

    By default, it does nothing with signals but provides underlying functionality.
    """

    def __init__(self, connections):
        self.connections = connections
        self.setup()

    def setup(self):
        """
        Set up.

        A hook for setting up anything necessary for ``handle_save/handle_delete`` to be executed.

        The default behavior is to do nothing (``pass``).
        """

    def teardown(self):
        """
        Tear down.

        A hook for tearing down anything necessary for ``handle_save/handle_delete`` to no longer be executed.

        The default behavior is to do nothing (``pass``).
        """

    def handle_m2m_changed(self, sender, instance, action, **kwargs):
        if action in {"post_add", "post_remove", "post_clear"}:
            self.handle_save(sender, instance)
        elif action in {"pre_remove", "pre_clear"}:
            self.handle_pre_delete(sender, instance)

    def handle_save(self, sender, instance, **kwargs):
        """
        Handle the saving.

        Given an individual model instance, update the object in the index.
        Update the related objects as well.
        """
        registry.update(instance)
        registry.update_related(instance)

    def handle_pre_delete(self, sender, instance, **kwargs):
        """
        Handle removing of instance object from related models instance.

        We need to do this before the real delete, otherwise the relation
        doesn't exist anymore, and we can't get the related models instance.
        """
        registry.delete_related(instance)

    def handle_delete(self, sender, instance, **kwargs):
        """
        Handle the deletion.

        Given an individual model instance, delete the object from index.
        """
        registry.delete(instance, raise_on_error=False)


class RealTimeSignalProcessor(BaseSignalProcessor):
    """
    Real-time signal processor.

    Allows for observing when saves/deletes fire and automatically updates the
    search engine appropriately.
    """

    def setup(self):
        # Listen to all model saves.
        models.signals.post_save.connect(self.handle_save)
        models.signals.post_delete.connect(self.handle_delete)

        # Use to manage related objects update
        models.signals.m2m_changed.connect(self.handle_m2m_changed)
        models.signals.pre_delete.connect(self.handle_pre_delete)

    def teardown(self):
        # Listen to all model saves.
        models.signals.post_save.disconnect(self.handle_save)
        models.signals.post_delete.disconnect(self.handle_delete)
        models.signals.m2m_changed.disconnect(self.handle_m2m_changed)
        models.signals.pre_delete.disconnect(self.handle_pre_delete)


try:
    from celery import shared_task
except ImportError:
    pass
else:

    class CelerySignalProcessor(RealTimeSignalProcessor):
        """
        Celery signal processor.

        Allows automatic updates on the index as delayed background tasks using Celery.
        """

        def handle_save(self, sender, instance, **kwargs):
            """
            Handle save with a Celery task.

            Given an individual model instance, update the object in the index.
            Update the related objects as well.

            ``post_save`` fires before an enclosing transaction commits. Enqueuing the task immediately lets a
            worker pick it up and read the row on another connection before it is visible there, so the index
            update silently applies stale (or missing) data. Inside an atomic block, defer enqueuing to
            ``transaction.on_commit`` so the task never runs ahead of the transaction it depends on.
            """
            if self.is_instance_indexed(instance):
                dispatch = partial(self.save.delay, *self.serialize_instance(instance))
                if connection.in_atomic_block:
                    transaction.on_commit(dispatch)
                else:
                    dispatch()

        def handle_pre_delete(self, sender, instance, **kwargs):
            """
            Handle removing of instance object from related models instance.

            We need to do this before the real delete, otherwise the relation
            doesn't exist anymore, and we can't get the related models instance.
            """
            if self.is_instance_indexed(instance):
                self.delete_related.delay(*self.serialize_instance(instance))

        def handle_delete(self, sender, instance, **kwargs):
            """
            Handle the deletion.

            Given an individual model instance, delete the object from the index.
            """
            if self.is_instance_indexed(instance):
                self.delete.delay(*self.serialize_instance(instance))

        @staticmethod
        def serialize_instance(instance) -> tuple[str, str, int]:
            """Get app label, model name and primary key from an instance."""
            return instance._meta.app_label, instance.__class__.__name__, instance.pk

        @staticmethod
        def deserialize_instance(app_label: str, model_name: str, pk: int):
            """Get an instance from app label, model name and primary key."""
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                return None
            try:
                return model.objects.get(pk=pk)
            except model.DoesNotExist:
                return None

        def is_instance_indexed(self, instance):
            """
            Check whether a change to this instance can affect any document.

            That is true both for models that have a document of their own and
            for models named in another document's ``related_models`` -- the
            latter have no document, yet a change to them must reindex the
            documents that embed them. Testing ``registry._models`` alone missed
            exactly that case, so the tasks that propagate related-model changes
            were never enqueued and embedded data went stale. ``registry``
            answers the broader question via ``__contains__``.
            """
            return instance.__class__ in registry

        @staticmethod
        @shared_task()
        def save(app_label, model_name, pk):
            """Handle the update on the registry as a Celery task."""
            instance = CelerySignalProcessor.deserialize_instance(app_label, model_name, pk)
            if instance:
                registry.update(instance)
                registry.update_related(instance)

        @staticmethod
        @shared_task()
        def delete_related(app_label, model_name, pk):
            """Handle the update on the registry as a Celery task."""
            instance = CelerySignalProcessor.deserialize_instance(app_label, model_name, pk)
            if instance:
                registry.delete_related(instance)

        @staticmethod
        @shared_task()
        def delete(app_label, model_name, pk):
            """
            Delete the document from the registry as a Celery task.

            By the time a worker picks up a delete task, the row is already gone, so unlike ``save``/
            ``delete_related`` this deliberately does not deserialize the instance from the database.
            ``registry.delete`` only needs the document id, and ``Document.generate_id`` derives that from the
            instance's pk alone, so an unsaved instance carrying just the pk is enough.

            Celery's at-least-once delivery means the same delete can be dispatched twice, and the document may
            already be gone by the second attempt -- that specific 404 is expected and swallowed. Any other
            bulk error is re-raised, same as an unhandled error from ``save``/``delete_related`` would be, so
            it surfaces through Celery's own task failure/retry handling instead of disappearing into a log
            line that may not be routed anywhere.
            """
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                return
            try:
                registry.delete(model(pk=pk))
            except BulkIndexError as exc:
                if not all(error.get("delete", {}).get("status") == HTTPStatus.NOT_FOUND for error in exc.errors):
                    raise
