# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_auto_20160607_0855'),
        ('workflows', '0007_auto_20160607_0821'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasktemplate',
            name='product_input_amount',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tasktemplate',
            name='product_input_measure',
            field=models.ForeignKey(to='inventory.AmountMeasure', default=1),
            preserve_default=False,
        ),
    ]
