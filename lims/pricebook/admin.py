from django.contrib import admin

from .models import PriceBook, Price

admin.site.register(PriceBook)
admin.site.register(Price)
