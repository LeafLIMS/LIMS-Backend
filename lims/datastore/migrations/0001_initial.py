# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0003_auto_20160906_0833'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('file_name', models.CharField(max_length=200)),
                ('location', models.CharField(max_length=200)),
                ('run_identifier', models.CharField(max_length=64)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('equipment', models.ForeignKey(to='equipment.Equipment')),
            ],
        ),
    ]
