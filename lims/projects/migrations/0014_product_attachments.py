# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datastore', '0005_attachment'),
        ('projects', '0013_auto_20161012_1259'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='attachments',
            field=models.ManyToManyField(blank=True, to='datastore.Attachment'),
        ),
    ]
