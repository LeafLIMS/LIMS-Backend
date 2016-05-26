from django.contrib import admin

from .models import CodonUsageTable, CodonUsage

admin.site.register(CodonUsageTable)
admin.site.register(CodonUsage)
