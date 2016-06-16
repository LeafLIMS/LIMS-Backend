# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.contrib.postgres.fields.ranges


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('status', models.CharField(choices=[('active', 'Active'), ('idle', 'Idle'), ('error', 'Error'), ('broken', 'Out of order')], max_length=30)),
                ('can_reserve', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='EquipmentReservation',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('start', models.DateTimeField(db_index=True)),
                ('end', models.DateTimeField(db_index=True)),
                ('reservation', django.contrib.postgres.fields.ranges.DateTimeRangeField(null=True)),
                ('reserved_for', models.CharField(blank=True, null=True, max_length=200)),
                ('is_confirmed', models.BooleanField(default=False)),
                ('checked_in', models.BooleanField(default=False)),
                ('confirmed_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('equipment_reserved', models.ForeignKey(to='equipment.Equipment')),
                ('reserved_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='reserved_by')),
            ],
        ),
    ]
