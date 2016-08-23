# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0010_product_design_format'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='design',
            field=models.TextField(null=True, blank=True),
        ),
    ]
