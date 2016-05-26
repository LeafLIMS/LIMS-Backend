# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import mptt.fields
import gm2m.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shared', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AmountMeasure',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('symbol', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='GenericItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('identifier', models.CharField(max_length=20, null=True, blank=True, unique=True, db_index=True)),
                ('metadata', jsonfield.fields.JSONField(null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('in_inventory', models.BooleanField(default=False)),
                ('amount_available', models.IntegerField(default=0)),
                ('added_on', models.DateTimeField(auto_now_add=True)),
                ('last_updated_on', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ItemType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=150, unique=True, db_index=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(null=True, to='inventory.ItemType', blank=True, related_name='children')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=6, null=True, unique=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(null=True, to='inventory.Location', blank=True, related_name='children')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PartType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('identifier', models.CharField(max_length=30, null=True, blank=True)),
                ('of_type', models.ForeignKey(null=True, blank=True, to='inventory.PartType')),
            ],
        ),
        migrations.CreateModel(
            name='Set',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('is_public', models.BooleanField(default=False)),
                ('is_partset', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Construct',
            fields=[
                ('genericitem_ptr', models.OneToOneField(auto_created=True, primary_key=True, to='inventory.GenericItem', parent_link=True, serialize=False)),
                ('sequence', models.TextField()),
                ('originating_organism', models.ForeignKey(to='shared.Organism')),
            ],
            bases=('inventory.genericitem',),
        ),
        migrations.CreateModel(
            name='Consumable',
            fields=[
                ('genericitem_ptr', models.OneToOneField(auto_created=True, primary_key=True, to='inventory.GenericItem', parent_link=True, serialize=False)),
            ],
            bases=('inventory.genericitem',),
        ),
        migrations.CreateModel(
            name='Enzyme',
            fields=[
                ('genericitem_ptr', models.OneToOneField(auto_created=True, primary_key=True, to='inventory.GenericItem', parent_link=True, serialize=False)),
                ('cut_sequence', models.CharField(max_length=50, null=True, blank=True)),
                ('recognition_sequence', models.CharField(max_length=50, null=True, blank=True)),
                ('effective_length', models.FloatField(null=True, blank=True)),
                ('overhang', models.CharField(max_length=20, null=True, blank=True)),
                ('methylation_sensitivity', models.CharField(max_length=50, null=True, blank=True)),
            ],
            bases=('inventory.genericitem',),
        ),
        migrations.CreateModel(
            name='Part',
            fields=[
                ('genericitem_ptr', models.OneToOneField(auto_created=True, primary_key=True, to='inventory.GenericItem', parent_link=True, serialize=False)),
                ('sequence', models.TextField()),
                ('usage', models.IntegerField(default=0)),
                ('optimised_for_organism', models.ForeignKey(null=True, to='shared.Organism', blank=True, related_name='optimised_for_organisms')),
                ('originating_organism', models.ForeignKey(to='shared.Organism', related_name='originating_organisms')),
            ],
            bases=('inventory.genericitem',),
        ),
        migrations.CreateModel(
            name='Primer',
            fields=[
                ('genericitem_ptr', models.OneToOneField(auto_created=True, primary_key=True, to='inventory.GenericItem', parent_link=True, serialize=False)),
                ('reference', models.CharField(max_length=50)),
                ('product', models.CharField(max_length=100, null=True, blank=True)),
                ('purification', models.CharField(max_length=100, null=True, blank=True)),
                ('primer_sequence', models.CharField(max_length=100)),
                ('gc_content', models.FloatField(verbose_name='GC content', null=True, blank=True)),
                ('tm_c', models.FloatField(verbose_name='Tm (50mM NaCl) C', null=True, blank=True)),
                ('nmoles', models.FloatField(null=True, blank=True)),
                ('modifications_and_services', models.CharField(max_length=100, null=True, blank=True)),
                ('nmoles_od', models.FloatField(verbose_name='nmoles/OD', null=True, blank=True)),
                ('microg_od', models.FloatField(verbose_name='μg/OD', null=True, blank=True)),
                ('bases', models.IntegerField(null=True, blank=True)),
            ],
            bases=('inventory.genericitem',),
        ),
        migrations.AddField(
            model_name='genericitem',
            name='added_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='genericitem',
            name='amount_measure',
            field=models.ForeignKey(to='inventory.AmountMeasure'),
        ),
        migrations.AddField(
            model_name='genericitem',
            name='item_type',
            field=mptt.fields.TreeForeignKey(to='inventory.ItemType'),
        ),
        migrations.AddField(
            model_name='genericitem',
            name='location',
            field=mptt.fields.TreeForeignKey(null=True, blank=True, to='inventory.Location'),
        ),
        migrations.AddField(
            model_name='genericitem',
            name='sets',
            field=gm2m.fields.GM2MField('inventory.Set', through_fields=('gm2m_src', 'gm2m_tgt', 'gm2m_ct', 'gm2m_pk'), related_name='items'),
        ),
        migrations.AddField(
            model_name='genericitem',
            name='tags',
            field=models.ManyToManyField(blank=True, to='inventory.Tag'),
        ),
    ]
