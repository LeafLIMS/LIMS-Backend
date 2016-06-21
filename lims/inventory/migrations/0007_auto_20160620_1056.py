# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0006_itemtransfer_date_created'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='itemtransfer',
            options={'ordering': ['-date_created']},
        ),
        migrations.AddField(
            model_name='itemtransfer',
            name='is_addition',
            field=models.BooleanField(default=False),
        ),
    ]
