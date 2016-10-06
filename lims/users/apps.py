from django.apps import AppConfig


class UserConfig(AppConfig):
    name = 'lims.users'

    def ready(self):
        import lims.users.signals  # noqa
