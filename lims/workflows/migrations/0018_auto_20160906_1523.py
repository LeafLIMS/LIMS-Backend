# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0017_auto_20160906_0947'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activeworkflow',
            name='product_statuses',
        ),
        migrations.RemoveField(
            model_name='activeworkflow',
            name='started_by',
        ),
        migrations.RemoveField(
            model_name='activeworkflow',
            name='workflow',
        ),
        migrations.RemoveField(
            model_name='workflowproduct',
            name='product',
        ),
        migrations.AddField(
            model_name='runlabware',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='ActiveWorkflow',
        ),
        migrations.DeleteModel(
            name='WorkflowProduct',
        ),
    ]
