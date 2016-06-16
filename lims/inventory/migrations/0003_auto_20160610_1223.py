# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_auto_20160607_0855'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemtransfer',
            name='run_identifier',
            field=models.CharField(null=True, max_length=64, blank=True),
        ),
        migrations.AlterField(
            model_name='itemtransfer',
            name='item',
            field=models.ForeignKey(to='inventory.Item', related_name='transfers'),
        ),
    ]
