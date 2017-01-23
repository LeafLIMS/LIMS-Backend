# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0015_auto_20170119_1542'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='concentration',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='item',
            name='concentration_measure',
            field=models.ForeignKey(to='inventory.AmountMeasure', null=True, blank=True, related_name='concentration_measure'),
        ),
    ]
