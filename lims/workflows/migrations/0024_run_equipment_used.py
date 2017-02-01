# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0004_equipmentreservation_reservation_details'),
        ('workflows', '0023_auto_20160927_1209'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='equipment_used',
            field=models.ForeignKey(to='equipment.Equipment', blank=True, null=True),
        ),
    ]
