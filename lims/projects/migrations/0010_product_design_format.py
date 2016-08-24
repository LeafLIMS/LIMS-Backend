# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0009_auto_20160722_0918'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='design_format',
            field=models.CharField(null=True, blank=True, choices=[('csv', 'CSV'), ('gb', 'GenBank')], max_length=20),
        ),
    ]
