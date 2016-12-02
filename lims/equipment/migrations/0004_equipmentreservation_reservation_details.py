# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0003_auto_20160906_0833'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentreservation',
            name='reservation_details',
            field=models.TextField(blank=True, null=True),
        ),
    ]
