# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0011_dataentry_item'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dataentry',
            options={'ordering': ['-date_created']},
        ),
        migrations.AddField(
            model_name='calculationfieldtemplate',
            name='result',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='dataentry',
            name='state',
            field=models.CharField(max_length=20, choices=[('active', 'In Progress'), ('succeeded', 'Succeded'), ('failed', 'Failed'), ('repeat succeeded', 'Repeat succeded'), ('repeat failed', 'Repeat Failed')]),
        ),
    ]
