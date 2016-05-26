# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shared', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodonUsage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=3)),
                ('value', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='CodonUsageTable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('species', models.ForeignKey(to='shared.Organism')),
            ],
        ),
        migrations.AddField(
            model_name='codonusage',
            name='table',
            field=models.ForeignKey(to='codonusage.CodonUsageTable', related_name='codons'),
        ),
    ]
