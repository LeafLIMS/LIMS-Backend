# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_auto_20160620_1056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='created_from',
            field=models.ManyToManyField(blank=True, to='inventory.Item'),
        ),
    ]
