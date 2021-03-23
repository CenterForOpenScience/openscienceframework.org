# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2021-03-23 17:16
from __future__ import unicode_literals

import addons.base.models
from django.db import migrations, models
import django_extensions.db.fields
import osf.models.base
import osf.utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NodeSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('_id', models.CharField(db_index=True, default=osf.models.base.generate_object_id, max_length=24, unique=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted', osf.utils.fields.NonNaiveDateTimeField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, addons.base.models.BaseStorageAddon),
        ),
        migrations.CreateModel(
            name='UserSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('_id', models.CharField(db_index=True, default=osf.models.base.generate_object_id, max_length=24, unique=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted', osf.utils.fields.NonNaiveDateTimeField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, osf.models.base.QuerySet),
        ),
    ]
