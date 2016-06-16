# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_product_design'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='linked_inventory',
            field=models.ManyToManyField(related_name='products', to='inventory.Item', blank=True),
        ),
    ]
