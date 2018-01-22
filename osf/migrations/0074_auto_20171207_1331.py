# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-07 19:31
from __future__ import unicode_literals

from django.db import migrations, models
import osf.models.validators


class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0073_citationstyle_has_bibliography'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='content',
            field=models.TextField(validators=[osf.models.validators.CommentMaxLength(1000), osf.models.validators.string_required]),
        ),
    ]
