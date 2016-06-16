# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('filetemplate', '0002_auto_20160613_1337'),
    ]

    operations = [
        migrations.AddField(
            model_name='filetemplate',
            name='file_for',
            field=models.CharField(max_length=6, choices=[('input', 'Input'), ('output', 'Output')], default='input'),
            preserve_default=False,
        ),
    ]
