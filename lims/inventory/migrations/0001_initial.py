# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import mptt.fields
import gm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AmountMeasure',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('symbol', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('identifier', models.CharField(unique=True, blank=True, null=True, db_index=True, max_length=20)),
                ('description', models.TextField(blank=True, null=True)),
                ('in_inventory', models.BooleanField(default=False)),
                ('amount_available', models.IntegerField(default=0)),
                ('added_on', models.DateTimeField(auto_now_add=True)),
                ('last_updated_on', models.DateTimeField(auto_now=True)),
                ('added_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('amount_measure', models.ForeignKey(to='inventory.AmountMeasure')),
                ('created_from', models.ManyToManyField(to='inventory.Item', blank=True, related_name='created_from_rel_+')),
            ],
        ),
        migrations.CreateModel(
            name='ItemProperty',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('value', models.TextField()),
                ('item', models.ForeignKey(to='inventory.Item', related_name='properties')),
            ],
        ),
        migrations.CreateModel(
            name='ItemTransfer',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('amount_taken', models.IntegerField(default=0)),
                ('barcode', models.CharField(blank=True, null=True, max_length=20)),
                ('coordinates', models.CharField(blank=True, null=True, max_length=2)),
                ('transfer_complete', models.BooleanField(default=False)),
                ('amount_measure', models.ForeignKey(to='inventory.AmountMeasure')),
                ('item', models.ForeignKey(to='inventory.Item')),
            ],
        ),
        migrations.CreateModel(
            name='ItemType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, db_index=True, max_length=150)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(null=True, related_name='children', to='inventory.ItemType', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(unique=True, null=True, max_length=6)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(null=True, related_name='children', to='inventory.Location', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Set',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('is_public', models.BooleanField(default=False)),
                ('is_partset', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=30)),
            ],
        ),
        migrations.AddField(
            model_name='item',
            name='item_type',
            field=mptt.fields.TreeForeignKey(to='inventory.ItemType'),
        ),
        migrations.AddField(
            model_name='item',
            name='location',
            field=mptt.fields.TreeForeignKey(null=True, to='inventory.Location', blank=True),
        ),
        migrations.AddField(
            model_name='item',
            name='sets',
            field=gm2m.fields.GM2MField('inventory.Set', through_fields=('gm2m_src', 'gm2m_tgt', 'gm2m_ct', 'gm2m_pk'), related_name='items'),
        ),
        migrations.AddField(
            model_name='item',
            name='tags',
            field=models.ManyToManyField(to='inventory.Tag', blank=True),
        ),
    ]
