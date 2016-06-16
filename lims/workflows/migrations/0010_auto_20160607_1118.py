# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_auto_20160607_0855'),
        ('workflows', '0009_auto_20160607_1047'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasktemplate',
            name='labware',
            field=models.ForeignKey(related_name='labware', to='inventory.ItemType', default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='tasktemplate',
            name='product_input',
            field=models.ForeignKey(related_name='product_input', to='inventory.ItemType'),
        ),
    ]
