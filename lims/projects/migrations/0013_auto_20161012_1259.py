# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0012_projectlink'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='projectlink',
            name='project',
        ),
        migrations.AddField(
            model_name='project',
            name='links',
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='ProjectLink',
        ),
    ]
