# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0019_auto_20170404_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemtransfer',
            name='amount_available',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='itemtransfer',
            name='amount_to_take',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='itemtransfer',
            name='has_taken',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
