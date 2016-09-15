# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0012_auto_20160912_1454'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='amount_available',
            field=models.FloatField(default=0),
        ),
    ]
