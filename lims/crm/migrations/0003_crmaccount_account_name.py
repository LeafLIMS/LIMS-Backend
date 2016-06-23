# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_auto_20160621_1456'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmaccount',
            name='account_name',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
    ]
