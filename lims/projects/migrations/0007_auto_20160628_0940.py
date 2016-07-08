# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def add_intital_product_statuses(apps, schema_editor):
    product_statuses = [
        'Added',
        'Submitted',
        'Received',
        'In Progress',
    ]
    ProductStatus = apps.get_model('projects', 'ProductStatus')
    for status in product_statuses:
        try:
            ps = ProductStatus(name=status)
            ps.save()
        except:
            pass

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_auto_20160628_0940'),
    ]

    operations = [
        migrations.RunPython(add_intital_product_statuses),
    ]
