from django.contrib import admin

from .models import Workflow, ActiveWorkflow, WorkflowProduct, DataEntry

admin.site.register(Workflow)
admin.site.register(ActiveWorkflow)
admin.site.register(WorkflowProduct)
admin.site.register(DataEntry)
