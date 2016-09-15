# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0019_auto_20160907_1522'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataentry',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='dataentry',
            name='data_files',
        ),
        migrations.RemoveField(
            model_name='dataentry',
            name='item',
        ),
        migrations.RemoveField(
            model_name='dataentry',
            name='product',
        ),
        migrations.RemoveField(
            model_name='dataentry',
            name='run',
        ),
        migrations.RemoveField(
            model_name='dataentry',
            name='task',
        ),
        migrations.DeleteModel(
            name='DataEntry',
        ),
    ]
