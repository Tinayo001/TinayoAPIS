# Generated by Django 5.1.4 on 2025-01-13 10:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('developers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='developerprofile',
            name='developer',
        ),
        migrations.AddField(
            model_name='developerprofile',
            name='address',
            field=models.TextField(default='Not provided'),
        ),
        migrations.AddField(
            model_name='developerprofile',
            name='developer_name',
            field=models.CharField(default='Unknown Developer', max_length=100),
        ),
        migrations.AddField(
            model_name='developerprofile',
            name='specialization',
            field=models.CharField(default='Elevators', max_length=255),
        ),
        migrations.AddField(
            model_name='developerprofile',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='developer_profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
