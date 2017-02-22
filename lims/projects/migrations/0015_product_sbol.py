# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0014_product_attachments'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sbol',
            field=models.TextField(blank=True, null=True),
        ),
    ]
