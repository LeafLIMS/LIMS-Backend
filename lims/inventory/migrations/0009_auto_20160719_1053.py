# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0008_auto_20160620_1306'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='sets',
        ),
        migrations.AddField(
            model_name='item',
            name='sets',
            field=models.ManyToManyField(blank=True, to='inventory.Set', related_name='items'),
        ),
    ]
