# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0014_auto_20161014_1320'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='wells',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='itemtransfer',
            name='linked_transfer',
            field=models.ForeignKey(to='inventory.ItemTransfer', blank=True, null=True),
        ),
    ]
