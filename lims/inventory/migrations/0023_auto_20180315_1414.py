# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-03-15 14:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0022_auto_20180305_1453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='code',
            field=models.CharField(max_length=12, null=True, unique=True),
        ),
    ]