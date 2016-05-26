# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Price',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=20)),
                ('price', models.FloatField()),
                ('identifier', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='PriceBook',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50, db_index=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('identifier', models.CharField(max_length=20, null=True)),
                ('prices', models.ManyToManyField(blank=True, to='pricebook.Price')),
            ],
        ),
    ]
