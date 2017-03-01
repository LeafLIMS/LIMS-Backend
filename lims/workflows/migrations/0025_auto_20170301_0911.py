# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0024_run_equipment_used'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasktemplate',
            name='labware_not_required',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='tasktemplate',
            name='labware',
            field=models.ForeignKey(null=True, related_name='labware', blank=True, to='inventory.ItemType'),
        ),
    ]
