# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0013_auto_20160808_1537'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasktemplate',
            name='multiple_products_on_labware',
            field=models.BooleanField(default=False),
        ),
    ]
