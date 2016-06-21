# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_auto_20160614_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemtransfer',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2016, 6, 16, 15, 8, 39, 328182, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
