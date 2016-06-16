# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0006_dataentry_run_identifier'),
    ]

    operations = [
        migrations.RenameField(
            model_name='activeworkflow',
            old_name='saved',
            new_name='task_state',
        ),
        migrations.AlterField(
            model_name='dataentry',
            name='state',
            field=models.CharField(choices=[('active', 'In Progress'), ('succeded', 'Succeded'), ('failed', 'Failed'), ('repeat succeded', 'Repeat succeded'), ('repeat failed', 'Repeat Failed')], max_length=20),
        ),
    ]
