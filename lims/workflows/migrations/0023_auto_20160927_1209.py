# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0022_tasktemplate_equipment_files'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='calculationfieldtemplate',
            options={'permissions': (('view_calculationfieldtemplate', 'View calculation field template'),)},
        ),
        migrations.AlterModelOptions(
            name='inputfieldtemplate',
            options={'permissions': (('view_inputfieldtemplate', 'View input field template'),)},
        ),
        migrations.AlterModelOptions(
            name='outputfieldtemplate',
            options={'permissions': (('view_outputfieldtemplate', 'View output field template'),)},
        ),
        migrations.AlterModelOptions(
            name='stepfieldtemplate',
            options={'permissions': (('view_stepfieldtemplate', 'View step field template'),)},
        ),
        migrations.AlterModelOptions(
            name='variablefieldtemplate',
            options={'permissions': (('view_variablefieldtemplate', 'View variable field template'),)},
        ),
    ]
