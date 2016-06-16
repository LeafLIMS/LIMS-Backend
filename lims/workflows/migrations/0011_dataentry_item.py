# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_auto_20160610_1223'),
        ('workflows', '0010_auto_20160607_1118'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataentry',
            name='item',
            field=models.ForeignKey(related_name='data_entries', to='inventory.Item', null=True),
        ),
    ]
