# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-07-08 20:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import osf.models.registrations


class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0209_branded_registries'),
    ]

    operations = [
        migrations.AlterField(
            model_name='draftregistration',
            name='provider',
            field=models.ForeignKey(default=osf.models.registrations.get_default_provider_id, on_delete=django.db.models.deletion.CASCADE, related_name='draft_registrations', to='osf.RegistrationProvider'),
        ),
    ]
