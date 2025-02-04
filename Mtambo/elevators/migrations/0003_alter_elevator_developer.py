# Generated by Django 5.1.4 on 2025-01-13 10:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('developers', '0002_remove_developerprofile_developer_and_more'),
        ('elevators', '0002_alter_elevator_maintenance_company_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='elevator',
            name='developer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='developed_elevators', to='developers.developerprofile'),
        ),
    ]
