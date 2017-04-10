# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datastore', '0005_attachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataentry',
            name='notes',
            field=models.TextField(null=True, blank=True),
        ),
    ]
