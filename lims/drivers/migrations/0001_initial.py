# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0003_auto_20160906_0833'),
    ]

    operations = [
        migrations.CreateModel(
            name='CopyFileDriver',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('copy_from_prefix', models.CharField(blank=True, null=True, max_length=200)),
                ('copy_to_prefix', models.CharField(blank=True, null=True, max_length=200)),
                ('is_enabled', models.BooleanField(default=True)),
                ('equipment', models.ForeignKey(to='equipment.Equipment')),
            ],
        ),
        migrations.CreateModel(
            name='CopyFilePath',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('copy_from', models.CharField(max_length=200)),
                ('copy_to', models.CharField(blank=True, null=True, max_length=200)),
                ('driver', models.ForeignKey(to='drivers.CopyFileDriver', related_name='locations')),
            ],
        ),
        migrations.CreateModel(
            name='Driver',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('class_path', models.CharField(default='lims.drivers.packages.core.DummyDriver', max_length=200)),
                ('is_enabled', models.BooleanField(default=True)),
                ('equipment', models.ForeignKey(to='equipment.Equipment')),
            ],
        ),
    ]
