# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_project_created_by'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'permissions': (('view_comment', 'View comment'),)},
        ),
        migrations.AlterModelOptions(
            name='productstatus',
            options={'permissions': (('view_productstatus', 'View product status'),)},
        ),
    ]
