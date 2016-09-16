# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('filetemplate', '0007_filetemplate_use_inputs'),
    ]

    operations = [
        migrations.AddField(
            model_name='filetemplate',
            name='total_inputs_only',
            field=models.BooleanField(default=False),
        ),
    ]
