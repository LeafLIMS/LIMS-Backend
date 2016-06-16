# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0002_auto_20160602_1431'),
    ]

    operations = [
        migrations.AddField(
            model_name='variablefieldtemplate',
            name='measure_not_required',
            field=models.BooleanField(default=False),
        ),
    ]
