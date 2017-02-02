# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0017_auto_20170131_1430'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemtransfer',
            name='barcode',
            field=models.CharField(null=True, max_length=20, db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='itemtransfer',
            name='run_identifier',
            field=models.UUIDField(null=True, db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='itemtransfer',
            name='transfer_complete',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
