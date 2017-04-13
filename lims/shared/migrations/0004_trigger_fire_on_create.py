# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shared', '0003_auto_20161109_1155'),
    ]

    operations = [
        migrations.AddField(
            model_name='trigger',
            name='fire_on_create',
            field=models.BooleanField(default=False),
        ),
    ]
