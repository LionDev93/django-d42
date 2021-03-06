# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-07 15:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_name', models.CharField(help_text="Example: 'signup_1.html'. The template to be tested.", max_length=255)),
                ('hits', models.IntegerField(default=0, help_text='# uniques that have seen this template.')),
                ('conversions', models.IntegerField(default=0, help_text='# uniques that have reached the goal from this test.')),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tests', to='device42_abtests.Experiment')),
            ],
        ),
    ]
