# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('filetemplate', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filetemplate',
            name='name',
            field=models.CharField(max_length=200, unique=True, db_index=True),
        ),
    ]
