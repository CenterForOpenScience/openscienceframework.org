# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-20 20:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0043_merge_20170725_1328'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nodelog',
            name='should_hide',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddIndex(
            model_name='nodelog',
            index=models.Index(fields=[b'node', b'should_hide', b'-date'], name='osf_nodelog_node_id_7b977c_idx'),
        ),
    ]
