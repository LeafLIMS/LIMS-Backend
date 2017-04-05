# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0025_auto_20170301_0911'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='exclude',
            field=models.CommaSeparatedIntegerField(null=True, blank=True, max_length=400),
        ),
    ]
