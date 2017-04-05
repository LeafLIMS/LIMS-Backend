# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0018_auto_20170201_1440'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='location',
            options={'ordering': ['tree_id', '-lft'], 'permissions': (('view_location', 'View location'),)},
        ),
    ]
