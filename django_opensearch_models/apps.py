from django.apps import AppConfig
from django.conf import settings
from django.utils.module_loading import import_string

from opensearchpy.connection import connections


class DEDConfig(AppConfig):
    name = 'django_opensearch_models'
    verbose_name = "Django opensearch models"
    signal_processor = None

    def ready(self):
        self.module.autodiscover()
        connections.configure(**settings.OPENSEARCH_DSL)
        # Setup the signal processor.
        if not self.signal_processor:
            signal_processor_path = getattr(
                settings,
                'OPENSEARCH_DSL_SIGNAL_PROCESSOR',
                'django_opensearch_models.signals.RealTimeSignalProcessor'
            )
            signal_processor_class = import_string(signal_processor_path)
            self.signal_processor = signal_processor_class(connections)

    @classmethod
    def autosync_enabled(cls):
        return getattr(settings, 'OPENSEARCH_DSL_AUTOSYNC', True)

    @classmethod
    def default_index_settings(cls):
        return getattr(settings, 'OPENSEARCH_DSL_INDEX_SETTINGS', {})

    @classmethod
    def auto_refresh_enabled(cls):
        return getattr(settings, 'OPENSEARCH_DSL_AUTO_REFRESH', True)
