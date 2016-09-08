# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0015_auto_20160906_0833'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='current_task',
            field=models.IntegerField(default=0, max_length=4),
        ),
        migrations.AddField(
            model_name='run',
            name='has_started',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='run',
            name='name',
            field=models.CharField(null=True, max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='run',
            name='task_in_progress',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='run',
            name='products',
            field=models.ManyToManyField(related_name='run', to='projects.Product', blank=True),
        ),
        migrations.AlterField(
            model_name='workflowproduct',
            name='product',
            field=models.OneToOneField(to='projects.Product', related_name='for_run'),
        ),
    ]
