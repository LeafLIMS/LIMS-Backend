# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='linked_inventory',
        ),
        migrations.AddField(
            model_name='product',
            name='linked_inventory',
            field=models.ManyToManyField(blank=True, to='inventory.Item'),
        ),
    ]
