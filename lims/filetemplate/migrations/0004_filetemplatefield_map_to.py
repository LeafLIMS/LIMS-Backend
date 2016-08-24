# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('filetemplate', '0003_filetemplate_file_for'),
    ]

    operations = [
        migrations.AddField(
            model_name='filetemplatefield',
            name='map_to',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
