# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_auto_20160614_1443'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='identifier',
            field=models.CharField(max_length=128, db_index=True, unique=True, null=True, blank=True),
        ),
    ]
