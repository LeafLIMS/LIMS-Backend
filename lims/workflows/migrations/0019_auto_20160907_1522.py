# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_auto_20160722_0918'),
        ('workflows', '0018_auto_20160906_1523'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataentry',
            name='task_run_identifier',
            field=models.UUIDField(db_index=True, default='daf01f65-bf52-44b8-937f-c35cfd1dbf68'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='run',
            name='task_run_identifier',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='run',
            name='transfers',
            field=models.ManyToManyField(to='inventory.ItemTransfer', blank=True, related_name='run_transfers'),
        ),
        migrations.AlterField(
            model_name='dataentry',
            name='run',
            field=models.ForeignKey(to='workflows.Run', null=True, related_name='data_entries'),
        ),
        migrations.AlterField(
            model_name='run',
            name='current_task',
            field=models.IntegerField(default=0),
        ),
    ]
