# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0020_auto_20160908_1454'),
    ]

    operations = [
        migrations.AlterField(
            model_name='run',
            name='products',
            field=models.ManyToManyField(blank=True, related_name='runs', to='projects.Product'),
        ),
    ]
