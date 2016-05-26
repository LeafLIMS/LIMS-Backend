# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CRMAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('contact_identifier', models.CharField(max_length=50)),
                ('account_identifier', models.CharField(max_length=50)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CRMProject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('project_identifier', models.CharField(max_length=50)),
                ('order', models.OneToOneField(null=True, to='orders.Order', related_name='crm')),
            ],
        ),
        migrations.CreateModel(
            name='CRMQuote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('quote_identifier', models.CharField(max_length=50)),
                ('quote_number', models.CharField(max_length=10)),
                ('quote_name', models.CharField(max_length=200)),
                ('subtotal', models.FloatField()),
                ('discount', models.FloatField(null=True, blank=True)),
                ('total', models.FloatField()),
                ('project', models.ForeignKey(to='crm.CRMProject', related_name='quotes')),
            ],
        ),
    ]
