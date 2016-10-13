# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_auto_20160822_1527'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('url', models.URLField()),
                ('display_name', models.CharField(blank=True, null=True, max_length=150)),
                ('project', models.ForeignKey(to='projects.Project', related_name='links')),
            ],
        ),
    ]
