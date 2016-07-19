from django.contrib import admin

from lims.shared.models import Organism
from .models import Tag, Set, ItemType, Item, AmountMeasure, Location


class ItemAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('name', 'description', 'get_tags',)

admin.site.register(Organism)
admin.site.register(Tag)
admin.site.register(Item, ItemAdmin)
admin.site.register(Set)
admin.site.register(ItemType)
admin.site.register(AmountMeasure)
admin.site.register(Location)
