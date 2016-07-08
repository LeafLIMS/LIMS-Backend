# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_project_crm_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productstatus',
            name='name',
            field=models.CharField(db_index=True, max_length=100, unique=True),
        ),
    ]
