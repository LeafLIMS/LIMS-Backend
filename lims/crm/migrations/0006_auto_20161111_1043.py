# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0005_auto_20161109_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crmproject',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
