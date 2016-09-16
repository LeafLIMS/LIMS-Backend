# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('filetemplate', '0006_auto_20160915_1454'),
        ('workflows', '0021_auto_20160912_1454'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasktemplate',
            name='equipment_files',
            field=models.ManyToManyField(to='filetemplate.FileTemplate', related_name='equipment_file_templates', blank=True),
        ),
    ]
