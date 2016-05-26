from django.contrib import admin

from .models import CRMAccount, CRMQuote, CRMProject

admin.site.register(CRMAccount)
admin.site.register(CRMProject)
admin.site.register(CRMQuote)
