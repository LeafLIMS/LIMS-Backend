# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='amountmeasure',
            name='name',
            field=models.CharField(unique=True, db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='amountmeasure',
            name='symbol',
            field=models.CharField(unique=True, db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='item',
            name='name',
            field=models.CharField(db_index=True, max_length=100),
        ),
    ]
