# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import gm2m.fields
import lims.projects.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventory', '0001_initial'),
        ('shared', '0001_initial'),
        ('orders', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('identifier', models.IntegerField(default=0)),
                ('name', models.CharField(max_length=200)),
                ('flag_issue', models.BooleanField(default=False)),
                ('product_identifier', models.CharField(default='', db_index=True, max_length=20)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('last_modified_on', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL)),
                ('linked_inventory', gm2m.fields.GM2MField(through_fields=('gm2m_src', 'gm2m_tgt', 'gm2m_ct', 'gm2m_pk'))),
                ('optimised_for', models.ForeignKey(null=True, to='shared.Organism', blank=True)),
                ('product_type', models.ForeignKey(to='inventory.ItemType')),
            ],
            options={
                'permissions': (('view_product', 'View product'),),
            },
        ),
        migrations.CreateModel(
            name='ProductStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('identifier', models.IntegerField(default=lims.projects.models.Project.create_identifier)),
                ('date_started', models.DateTimeField(auto_now_add=True)),
                ('archive', models.BooleanField(default=False)),
                ('project_identifier', models.CharField(default='', max_length=20)),
                ('order', models.ForeignKey(null=True, related_name='associated_projects', to='orders.Order', blank=True)),
                ('primary_lab_contact', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': (('view_project', 'View project'),),
            },
        ),
        migrations.CreateModel(
            name='WorkLog',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('task', models.CharField(max_length=200)),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('finish_time', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(to='projects.Project')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='project',
            field=models.ForeignKey(to='projects.Project'),
        ),
        migrations.AddField(
            model_name='product',
            name='status',
            field=models.ForeignKey(to='projects.ProductStatus'),
        ),
        migrations.AddField(
            model_name='comment',
            name='product',
            field=models.ForeignKey(to='projects.Product'),
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
