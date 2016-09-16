# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('filetemplate', '0005_filetemplatefield_is_property'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filetemplate',
            name='file_for',
            field=models.CharField(max_length=6, choices=[('input', 'Input'), ('equip', 'Equipment'), ('output', 'Output')]),
        ),
    ]
