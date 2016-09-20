# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datastore', '0002_dataentry'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datafile',
            name='run_identifier',
        ),
    ]
