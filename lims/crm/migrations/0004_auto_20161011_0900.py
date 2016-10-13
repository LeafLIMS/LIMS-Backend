# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_crmaccount_account_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='crmaccount',
            options={'permissions': (('view_crmaccount', 'View CRM Account'),)},
        ),
        migrations.AlterModelOptions(
            name='crmproject',
            options={'permissions': (('view_crmproject', 'View CRM Project'),)},
        ),
        migrations.AlterModelOptions(
            name='crmquote',
            options={'permissions': (('view_crmquote', 'View CRM Quote'),)},
        ),
        migrations.AddField(
            model_name='crmproject',
            name='status',
            field=models.CharField(max_length=100, blank=True, default=''),
        ),
    ]
