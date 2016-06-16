# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0002_equipment_location'),
        ('inventory', '0001_initial'),
        ('projects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('filetemplate', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActiveWorkflow',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('date_started', models.DateTimeField(auto_now_add=True)),
                ('saved', jsonfield.fields.JSONField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-date_started'],
                'permissions': (('view_activeworkflow', 'View activeworkflow'),),
            },
        ),
        migrations.CreateModel(
            name='CalculationFieldTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('label', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, null=True, max_length=200)),
                ('calculation', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='DataEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('state', models.CharField(choices=[('succeded', 'Succeded'), ('failed', 'Failed'), ('repeat succeded', 'Repeat succeded'), ('repeat failed', 'Repeat Failed')], max_length=20)),
                ('data', jsonfield.fields.JSONField(default=dict)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(to='projects.Product', related_name='data')),
            ],
        ),
        migrations.CreateModel(
            name='InputFieldTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('label', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, null=True, max_length=200)),
                ('amount', models.FloatField()),
                ('from_input_file', models.BooleanField(default=False)),
                ('from_calculation', models.BooleanField(default=False)),
                ('calculation_used', models.ForeignKey(null=True, to='workflows.CalculationFieldTemplate', blank=True)),
                ('lookup_type', models.ForeignKey(to='inventory.ItemType')),
                ('measure', models.ForeignKey(to='inventory.AmountMeasure')),
            ],
        ),
        migrations.CreateModel(
            name='OutputFieldTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('label', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, null=True, max_length=200)),
                ('amount', models.FloatField()),
                ('from_calculation', models.BooleanField(default=False)),
                ('calculation_used', models.ForeignKey(null=True, to='workflows.CalculationFieldTemplate', blank=True)),
                ('lookup_type', models.ForeignKey(to='inventory.ItemType')),
                ('measure', models.ForeignKey(to='inventory.AmountMeasure')),
            ],
        ),
        migrations.CreateModel(
            name='StepFieldProperty',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('label', models.CharField(max_length=50)),
                ('amount', models.FloatField()),
                ('measure', models.ForeignKey(to='inventory.AmountMeasure')),
            ],
        ),
        migrations.CreateModel(
            name='StepFieldTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('label', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, null=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='TaskTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('capable_equipment', models.ManyToManyField(to='equipment.Equipment', blank=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('input_files', models.ManyToManyField(to='filetemplate.FileTemplate', blank=True, related_name='input_file_templates')),
                ('output_files', models.ManyToManyField(to='filetemplate.FileTemplate', blank=True, related_name='output_file_templates')),
                ('product_input', models.ForeignKey(to='inventory.ItemType')),
            ],
            options={
                'permissions': (('view_workflowtask', 'View workflowtask'),),
            },
        ),
        migrations.CreateModel(
            name='VariableFieldTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('label', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, null=True, max_length=200)),
                ('amount', models.FloatField()),
                ('measure', models.ForeignKey(to='inventory.AmountMeasure')),
                ('template', models.ForeignKey(to='workflows.TaskTemplate', related_name='variable_fields')),
            ],
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('order', models.CommaSeparatedIntegerField(blank=True, max_length=200)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': (('view_workflow', 'View workflow'),),
            },
        ),
        migrations.CreateModel(
            name='WorkflowProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('current_task', models.IntegerField(default=0)),
                ('task_in_progress', models.BooleanField(default=False)),
                ('product', models.OneToOneField(related_name='on_workflow_as', to='projects.Product')),
            ],
        ),
        migrations.AddField(
            model_name='stepfieldtemplate',
            name='template',
            field=models.ForeignKey(to='workflows.TaskTemplate', related_name='step_fields'),
        ),
        migrations.AddField(
            model_name='stepfieldproperty',
            name='step',
            field=models.ForeignKey(to='workflows.StepFieldTemplate', related_name='properties'),
        ),
        migrations.AddField(
            model_name='outputfieldtemplate',
            name='template',
            field=models.ForeignKey(to='workflows.TaskTemplate', related_name='output_fields'),
        ),
        migrations.AddField(
            model_name='inputfieldtemplate',
            name='template',
            field=models.ForeignKey(to='workflows.TaskTemplate', related_name='input_fields'),
        ),
        migrations.AddField(
            model_name='dataentry',
            name='task',
            field=models.ForeignKey(to='workflows.TaskTemplate'),
        ),
        migrations.AddField(
            model_name='dataentry',
            name='workflow',
            field=models.ForeignKey(to='workflows.Workflow'),
        ),
        migrations.AddField(
            model_name='calculationfieldtemplate',
            name='template',
            field=models.ForeignKey(to='workflows.TaskTemplate', related_name='calculation_fields'),
        ),
        migrations.AddField(
            model_name='activeworkflow',
            name='products',
            field=models.ManyToManyField(to='workflows.WorkflowProduct', blank=True, related_name='activeworkflow'),
        ),
        migrations.AddField(
            model_name='activeworkflow',
            name='started_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='activeworkflow',
            name='workflow',
            field=models.ForeignKey(to='workflows.Workflow'),
        ),
    ]
