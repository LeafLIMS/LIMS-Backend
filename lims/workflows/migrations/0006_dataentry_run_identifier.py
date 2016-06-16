# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0005_auto_20160603_1041'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataentry',
            name='run_identifier',
            field=models.CharField(default='', db_index=True, max_length=64),
            preserve_default=False,
        ),
    ]
