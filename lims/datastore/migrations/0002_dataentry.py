# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_auto_20160722_0918'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0011_auto_20160822_1527'),
        ('workflows', '0020_auto_20160908_1454'),
        ('datastore', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('task_run_identifier', models.UUIDField(db_index=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('state', models.CharField(max_length=20, choices=[('active', 'In Progress'), ('succeeded', 'Succeded'), ('failed', 'Failed'), ('repeat succeeded', 'Repeat succeded'), ('repeat failed', 'Repeat Failed')])),
                ('data', jsonfield.fields.JSONField(default=dict)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('data_files', models.ManyToManyField(to='datastore.DataFile', blank=True)),
                ('item', models.ForeignKey(related_name='data_entries', to='inventory.Item', null=True)),
                ('product', models.ForeignKey(to='projects.Product', related_name='data')),
                ('run', models.ForeignKey(related_name='data_entries', to='workflows.Run', null=True)),
                ('task', models.ForeignKey(to='workflows.TaskTemplate')),
            ],
            options={
                'ordering': ['-date_created'],
            },
        ),
    ]
