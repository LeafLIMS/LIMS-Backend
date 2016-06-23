# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmproject',
            name='account',
            field=models.ForeignKey(to='crm.CRMAccount', default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='crmproject',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2016, 6, 21, 14, 56, 11, 617716, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='crmproject',
            name='description',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='crmproject',
            name='name',
            field=models.CharField(default='none', max_length=300),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='crmproject',
            name='order',
            field=models.OneToOneField(blank=True, to='orders.Order', null=True, related_name='crm'),
        ),
    ]
