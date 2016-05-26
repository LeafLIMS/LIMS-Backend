# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('status', models.CharField(max_length=100)),
                ('data', jsonfield.fields.JSONField(default=dict)),
                ('status_bar_status', models.CharField(max_length=30, default='Submitted', choices=[('Submitted', 'Submitted'), ('Quote Sent', 'Quote Sent'), ('Order Received', 'Order Received'), ('Project in Progress', 'Project in Progress'), ('Project Shipped', 'Project Shipped')])),
                ('date_placed', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('is_quote', models.BooleanField(default=False)),
                ('quote_sent', models.BooleanField(default=False)),
                ('po_receieved', models.BooleanField(verbose_name='Purchase order receieved', default=False)),
                ('po_reference', models.CharField(max_length=50, null=True, blank=True)),
                ('invoice_sent', models.BooleanField(default=False)),
                ('has_paid', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-date_updated'],
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=20, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='services',
            field=models.ManyToManyField(to='orders.Service'),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
