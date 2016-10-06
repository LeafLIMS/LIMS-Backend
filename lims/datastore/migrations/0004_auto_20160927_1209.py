# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datastore', '0003_remove_datafile_run_identifier'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataentry',
            name='state',
            field=models.CharField(max_length=20, choices=[('active', 'In Progress'), ('succeeded', 'Succeeded'), ('failed', 'Failed'), ('repeat succeeded', 'Repeat succeeded'), ('repeat failed', 'Repeat Failed')]),
        ),
    ]
