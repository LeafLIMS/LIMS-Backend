# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FileTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=200, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='FileTemplateField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('required', models.BooleanField(default=False)),
                ('is_identifier', models.BooleanField(default=False)),
                ('template', models.ForeignKey(to='filetemplate.FileTemplate', related_name='fields')),
            ],
        ),
    ]
