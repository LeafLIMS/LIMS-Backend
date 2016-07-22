# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0010_auto_20160721_0902'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='amountmeasure',
            options={'permissions': (('view_amountmeasure', 'View measure'),)},
        ),
        migrations.AlterModelOptions(
            name='itemtype',
            options={'permissions': (('view_itemtype', 'View item type'),)},
        ),
        migrations.AlterModelOptions(
            name='location',
            options={'permissions': (('view_location', 'View location'),)},
        ),
        migrations.AlterModelOptions(
            name='set',
            options={'permissions': (('view_set', 'View item set'),)},
        ),
    ]
