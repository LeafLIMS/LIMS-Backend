# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_auto_20160722_0918'),
        ('datastore', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workflows', '0014_tasktemplate_multiple_products_on_labware'),
    ]

    operations = [
        migrations.CreateModel(
            name='Run',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('tasks', models.CommaSeparatedIntegerField(blank=True, max_length=400)),
                ('identifier', models.UUIDField(editable=False, default=uuid.uuid4)),
                ('is_active', models.BooleanField(default=False)),
                ('date_started', models.DateTimeField(auto_now_add=True)),
                ('date_finished', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-date_started'],
                'permissions': (('view_run', 'View run'),),
            },
        ),
        migrations.CreateModel(
            name='RunLabware',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('identifier', models.CharField(db_index=True, max_length=100)),
                ('labware', models.ForeignKey(to='inventory.Item')),
            ],
        ),
        migrations.RemoveField(
            model_name='workflowproduct',
            name='run_identifier',
        ),
        migrations.AddField(
            model_name='dataentry',
            name='data_files',
            field=models.ManyToManyField(to='datastore.DataFile', blank=True),
        ),
        migrations.AddField(
            model_name='tasktemplate',
            name='labware_amount',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='run',
            name='labware',
            field=models.ManyToManyField(to='workflows.RunLabware', blank=True, related_name='run_labware'),
        ),
        migrations.AddField(
            model_name='run',
            name='products',
            field=models.ManyToManyField(to='workflows.WorkflowProduct', blank=True, related_name='run'),
        ),
        migrations.AddField(
            model_name='run',
            name='started_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
