# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('filetemplate', '0006_auto_20160915_1454'),
    ]

    operations = [
        migrations.AddField(
            model_name='filetemplate',
            name='use_inputs',
            field=models.BooleanField(default=False),
        ),
    ]
