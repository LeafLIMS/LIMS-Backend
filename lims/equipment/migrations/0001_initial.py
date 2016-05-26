# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields.ranges
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('status', models.CharField(max_length=30, choices=[('active', 'Active'), ('idle', 'Idle'), ('error', 'Error'), ('broken', 'Out of order')])),
                ('can_reserve', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='EquipmentReservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('start', models.DateTimeField(db_index=True)),
                ('end', models.DateTimeField(db_index=True)),
                ('reservation', django.contrib.postgres.fields.ranges.DateTimeRangeField(null=True)),
                ('reserved_for', models.CharField(max_length=200, null=True, blank=True)),
                ('is_confirmed', models.BooleanField(default=False)),
                ('checked_in', models.BooleanField(default=False)),
                ('confirmed_by', models.ForeignKey(null=True, blank=True, to=settings.AUTH_USER_MODEL)),
                ('equipment_reserved', models.ForeignKey(to='equipment.Equipment')),
                ('reserved_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='reserved_by')),
            ],
        ),
    ]
