from django.contrib import admin

from .models import (Organism, Tag, Part, Set, ItemType, PartType, 
    Primer, Enzyme, Consumable, AmountMeasure, Location)

class PartAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('name', 'description', 'get_part_types', 'get_tags',)

class ItemAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('name', 'description', 'get_tags',)

admin.site.register(Organism)
admin.site.register(Tag)
admin.site.register(Part, PartAdmin)
admin.site.register(Primer, ItemAdmin)
admin.site.register(Enzyme, ItemAdmin)
admin.site.register(Set)
admin.site.register(PartType)
admin.site.register(ItemType)
admin.site.register(Consumable)
admin.site.register(AmountMeasure)
admin.site.register(Location)
