# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shared', '0002_limspermission'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trigger',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('field', models.CharField(default='id', max_length=80)),
                ('operator', models.CharField(default='==', choices=[('<', 'less than'), ('<=', 'less than or equal to'), ('==', 'equal to'), ('>=', 'greater than or equal to'), ('>', 'greater than'), ('!=', 'not equal to')], max_length=2)),
                ('value', models.CharField(default='1', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='TriggerAlert',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('fired', models.DateTimeField(auto_now_add=True)),
                ('instance_id', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='TriggerAlertStatus',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('status', models.CharField(default='A', choices=[('A', 'Active'), ('S', 'Silenced'), ('D', 'Dismissed')], max_length=1)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('last_updated_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, blank=True, null=True, related_name='updatedalerts')),
                ('triggeralert', models.ForeignKey(to='shared.TriggerAlert', related_name='statuses')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='alerts')),
            ],
        ),
        migrations.CreateModel(
            name='TriggerSet',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('model', models.CharField(default='Item', max_length=80)),
                ('severity', models.CharField(default='L', choices=[('L', 'low'), ('M', 'medium'), ('H', 'high')], max_length=1)),
                ('name', models.TextField(default='My Trigger')),
                ('email_title', models.CharField(default='Alert from GET LIMS', max_length=255)),
                ('email_template', models.TextField(default='{name}: {model} instance {instance} triggered on {date}.')),
            ],
        ),
        migrations.CreateModel(
            name='TriggerSubscription',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('email', models.BooleanField(default=False)),
                ('triggerset', models.ForeignKey(to='shared.TriggerSet', related_name='subscriptions')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='triggeralert',
            name='triggerset',
            field=models.ForeignKey(to='shared.TriggerSet', related_name='alerts'),
        ),
        migrations.AddField(
            model_name='trigger',
            name='triggerset',
            field=models.ForeignKey(to='shared.TriggerSet', related_name='triggers'),
        ),
    ]
