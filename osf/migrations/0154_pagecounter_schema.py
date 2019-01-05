# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-10 18:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0153_merge_20181221_1842'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagecounter',
            name='action',
            field=models.CharField(default=b'download', max_length=128),
        ),
        migrations.AddField(
            model_name='pagecounter',
            name='file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pagecounters', to='osf.BaseFileNode'),
        ),
        migrations.AddField(
            model_name='pagecounter',
            name='resource',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pagecounters', to='osf.Guid'),
        ),
        migrations.AddField(
            model_name='pagecounter',
            name='version',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
