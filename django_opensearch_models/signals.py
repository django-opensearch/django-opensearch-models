"""A convenient way to attach django-opensearch-models to Django's signals and cause things to index."""

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.dispatch import Signal
from django.utils.module_loading import import_string
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

        NB: We cannot process deletes as background tasks.
        By the time the Celery worker would pick up the delete job, the model instance would be already deleted.
        We can get around this by setting Celery to use `pickle` and sending the object to the worker,
        but using `pickle` opens the application up to security concerns.
        """

        def handle_save(self, sender, instance, **kwargs):
            """
            Handle save with a Celery task.

            Given an individual model instance, update the object in the index.
            Update the related objects as well.
            """
            pk = instance.pk
            app_label = instance._meta.app_label
            model_name = instance.__class__.__name__
            self.registry_update_task.delay(pk, app_label, model_name)
            self.registry_update_related_task.delay(pk, app_label, model_name)

        def handle_pre_delete(self, sender, instance, **kwargs):
            """
            Handle removing of instance object from related models instance.

            We need to do this before the real delete, otherwise the relation
            doesn't exist anymore, and we can't get the related models instance.
            """
            action = "index"
            for doc in registry._get_related_doc(instance):
                doc_instance = doc(related_instance_to_ignore=instance)
                try:
                    related = doc_instance.get_instances_from_related(instance)
                except ObjectDoesNotExist:
                    related = None
                if related is not None:
                    doc_instance.update(related)
                    object_list = [related] if isinstance(related, models.Model) else related
                    bulk_data = list(doc_instance._get_actions(object_list, action))
                    self.registry_delete_task.delay(self.get_full_qualname(doc_instance), bulk_data)

        def handle_delete(self, sender, instance, **kwargs):
            """
            Handle the deletion.

            Given an individual model instance, delete the object from the index.
            """
            action = "delete"
            for doc in registry._get_related_doc(instance):
                doc_instance = doc(related_instance_to_ignore=instance)
                try:
                    related = doc_instance.get_instances_from_related(instance)
                except ObjectDoesNotExist:
                    related = None
                if related is not None:
                    doc_instance.update(related)
                    object_list = [related] if isinstance(related, models.Model) else related
                    bulk_data = list(doc_instance.get_actions(object_list, action))
                    self.registry_delete_task.delay(self.get_full_qualname(doc_instance), bulk_data)

        def get_full_qualname(self, doc_instance):
            """Get the full qualified name of the instance's class."""
            return f"{doc_instance.__class__.__module__}.{doc_instance.__class__.__name__}"

        @staticmethod
        @shared_task()
        def registry_delete_task(doc_label, bulk_data):
            """
            Handle the bulk delete data on the registry as a Celery task.

            The different implementations used are due to the difference between delete and update operations.
            The update operation can re-read the updated data from the database to ensure eventual consistency,
            but the deletion needs to be processed before the database record is deleted to get the associated data.
            """
            doc_instance = import_string(doc_label)()
            parallel = True
            doc_instance._bulk(bulk_data, parallel=parallel)

        @staticmethod
        @shared_task()
        def registry_update_task(pk, app_label, model_name):
            """Handle the update on the registry as a Celery task."""
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                return
            try:
                registry.update(model.objects.get(pk=pk))
            except model.DoesNotExist:
                return

        @staticmethod
        @shared_task()
        def registry_update_related_task(pk, app_label, model_name):
            """Handle the related update on the registry as a Celery task."""
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                return
            try:
                registry.update_related(model.objects.get(pk=pk))
            except model.DoesNotExist:
                return
