from django.contrib import admin

from .models import Order, Service

# Register your models here.
admin.site.register(Order)
admin.site.register(Service)
