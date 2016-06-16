# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0008_auto_20160607_0855'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activeworkflow',
            name='task_state',
        ),
        migrations.AddField(
            model_name='workflowproduct',
            name='run_identifier',
            field=models.CharField(db_index=True, max_length=64, default=''),
            preserve_default=False,
        ),
    ]
