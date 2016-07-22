# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0009_auto_20160719_1053'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='item',
            options={'permissions': (('view_item', 'View item'),)},
        ),
    ]
