# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0004_auto_20161011_0900'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crmaccount',
            name='account_identifier',
            field=models.CharField(max_length=50, blank=True, null=True),
        ),
    ]
