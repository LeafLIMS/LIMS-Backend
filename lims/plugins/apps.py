from django.apps import AppConfig
from lims.plugins.mounts import load_plugins


class PluginsConfig(AppConfig):
    name = 'lims.plugins'
    verbose_name = 'Plugins'

    def ready(self):
        load_plugins()
