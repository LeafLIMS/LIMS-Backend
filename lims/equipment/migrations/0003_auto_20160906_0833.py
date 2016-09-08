# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0002_equipment_location'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='equipment',
            options={'ordering': ['id']},
        ),
        migrations.AlterField(
            model_name='equipment',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('idle', 'Idle'), ('error', 'Error'), ('broken', 'Out of order')], default='idle', max_length=30),
        ),
        migrations.AlterField(
            model_name='equipmentreservation',
            name='equipment_reserved',
            field=models.ForeignKey(to='equipment.Equipment', related_name='reservations'),
        ),
    ]
