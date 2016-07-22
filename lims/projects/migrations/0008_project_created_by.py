# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0007_auto_20160628_0940'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, default=1, related_name='created_by'),
            preserve_default=False,
        ),
    ]
