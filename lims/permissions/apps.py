from django.apps import AppConfig


class PermissionsConfig(AppConfig):
    def ready(self):
        import lims.permissions.signals  # noqa
