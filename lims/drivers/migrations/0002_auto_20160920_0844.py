# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('drivers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='copyfiledriver',
            name='equipment',
            field=models.ForeignKey(related_name='files_to_copy', to='equipment.Equipment'),
        ),
    ]
