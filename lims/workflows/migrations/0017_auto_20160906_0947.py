# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0016_auto_20160906_0941'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataentry',
            name='run_identifier',
        ),
        migrations.RemoveField(
            model_name='dataentry',
            name='workflow',
        ),
        migrations.RemoveField(
            model_name='run',
            name='identifier',
        ),
        migrations.AddField(
            model_name='dataentry',
            name='run',
            field=models.ForeignKey(to='workflows.Run', null=True),
        ),
        migrations.AlterField(
            model_name='run',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
