# Generated by Django 2.2 on 2021-03-18 17:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('addons_gitlab', '0001_initial'),
        ('osf', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='owner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='addons_gitlab_user_settings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='nodesettings',
            name='external_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='addons_gitlab_node_settings', to='osf.ExternalAccount'),
        ),
        migrations.AddField(
            model_name='nodesettings',
            name='owner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='addons_gitlab_node_settings', to='osf.AbstractNode'),
        ),
        migrations.AddField(
            model_name='nodesettings',
            name='user_settings',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='addons_gitlab.UserSettings'),
        ),
    ]
