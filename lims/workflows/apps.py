from django.apps import AppConfig


class WorkflowsConfig(AppConfig):
    name = 'lims.workflows'

    def ready(self):
        import lims.workflows.signals  # noqa
