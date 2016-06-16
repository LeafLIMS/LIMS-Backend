# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0004_auto_20160602_1457'),
    ]

    operations = [
        migrations.RenameField(
            model_name='activeworkflow',
            old_name='products',
            new_name='product_statuses',
        ),
    ]
