# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0003_variablefieldtemplate_measure_not_required'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variablefieldtemplate',
            name='measure',
            field=models.ForeignKey(to='inventory.AmountMeasure', blank=True, null=True),
        ),
    ]
