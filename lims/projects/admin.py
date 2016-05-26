from django.contrib import admin

from .models import Project, Product, Comment, WorkLog

admin.site.register(Project)
admin.site.register(Product)
admin.site.register(Comment)
admin.site.register(WorkLog)
