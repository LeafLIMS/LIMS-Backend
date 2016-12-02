import sys

from django.apps import AppConfig
from django.db.models.signals import post_save


class SharedConfig(AppConfig):
    name = 'lims.shared'

    def ready(self):
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv:
            from lims.shared.models import TriggerSet
            post_save.connect(TriggerSet()._fire_triggersets, dispatch_uid='Fire Trigger Sets')
