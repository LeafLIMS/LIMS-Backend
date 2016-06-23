# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_crmaccount_account_name'),
        ('projects', '0004_auto_20160613_1337'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='crm_project',
            field=models.ForeignKey(null=True, blank=True, to='crm.CRMProject'),
        ),
    ]
