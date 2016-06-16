# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stepfieldproperty',
            name='calculation_used',
            field=models.ForeignKey(blank=True, null=True, to='workflows.CalculationFieldTemplate'),
        ),
        migrations.AddField(
            model_name='stepfieldproperty',
            name='from_calculation',
            field=models.BooleanField(default=False),
        ),
    ]
