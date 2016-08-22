# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('filetemplate', '0004_filetemplatefield_map_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='filetemplatefield',
            name='is_property',
            field=models.BooleanField(default=False),
        ),
    ]
