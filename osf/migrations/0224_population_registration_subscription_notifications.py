# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-10-26 18:43
from __future__ import unicode_literals

from django.db import migrations

from osf.management.commands import populate_registration_provider_notification_subscriptions

def revert(apps, schema_editor):
    NotificationSubscription = apps.get_model('osf', 'NotificationSubscription')
    # The revert of this migration deletes all NotificationSubscription instances
    NotificationSubscription.objects.filter(provider__isnull=False, provider__type='osf.registrationprovider').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0223_auto_20201026_1843'),
    ]

    operations = [
        migrations.RunPython(populate_registration_provider_notification_subscriptions, revert)
    ]
