# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_auto_20160722_0918'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itemtransfer',
            name='run_identifier',
        ),
        migrations.AddField(
            model_name='itemtransfer',
            name='run_identifier',
            field=models.UUIDField(blank=True, null=True),
            preserve_default=False,
        ),
    ]
