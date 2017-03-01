# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def make_locations(apps, schema_editor):
    Location = apps.get_model('inventory', 'Location')
    default_locations = [
        ('Lab', 'L', 1,),
    ]
    for item in default_locations:
        l = Location(name=item[0], code=item[1], lft=0, rght=0, level=0, tree_id=item[2])
        l.save()

def make_measures(apps, schema_editor):
    AmountMeasure = apps.get_model('inventory', 'AmountMeasure')
    default_measures = [
        ('Litres', 'l'),
        ('Millilitres', 'ml'),
        ('Microlitres', 'ul'),
        ('Nanolitres', 'nl'),
        ('Metres', 'm'),
        ('Centimetres', 'cm'),
        ('Millimetres', 'mm'),
        ('Micrometres', 'um'),
        ('Nanometres', 'nm'),
        ('Millimolar', 'mM'),
        ('Micromolar', 'uM'),
        ('Nanomolar', 'nM'),
        ('Kilogram', 'kg'),
        ('Gram', 'g'),
        ('Milligram', 'mg'),
        ('Microgram', 'ug'),
        ('Nanogram', 'ng'),
        ('Day', 'day'),
        ('Hour', 'hr'),
        ('Minute', 'min'),
        ('Second', 's'),
        ('Millisecond', 'ms'),
        ('Kelvin', 'K'),
        ('Celsius', '°C'),
        ('Microsecond', 'us'),
        ('Nanosecond', 'ns'),
        ('Microgram/microlitre', 'ug/ul'),
        ('Item', 'item'),
    ]
    for item in default_measures:
        AmountMeasure.objects.create(name=item[0], symbol=item[1])

def make_itemtypes(apps, schema_editor):
    ItemType = apps.get_model('inventory', 'ItemType')
    default_itemtypes = [
        ('Item',)
    ]
    for item in default_itemtypes:
         itm = ItemType(name=item[0], lft=0, rght=0, level=0, tree_id=0)
         itm.save()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0016_auto_20170123_0941'),
    ]

    operations = [
        migrations.RunPython(make_measures),
        migrations.RunPython(make_locations),
        migrations.RunPython(make_itemtypes),
    ]
