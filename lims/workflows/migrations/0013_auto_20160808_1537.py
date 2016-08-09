# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0012_auto_20160711_0905'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tasktemplate',
            options={'permissions': (('view_tasktemplate', 'View workflow task template'),)},
        ),
    ]
