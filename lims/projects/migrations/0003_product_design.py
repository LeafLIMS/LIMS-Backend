# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_auto_20160601_0821'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='design',
            field=models.FileField(null=True, blank=True, upload_to=''),
        ),
    ]
