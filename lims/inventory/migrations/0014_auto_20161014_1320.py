# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0013_auto_20160915_1055'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='barcode',
            field=models.CharField(blank=True, null=True, db_index=True, max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='identifier',
            field=models.CharField(blank=True, null=True, max_length=200, db_index=True),
        ),
    ]
