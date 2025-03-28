# Generated by Django 5.1.4 on 2025-01-20 09:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elevators', '0003_alter_elevator_developer'),
        ('maintenance_companies', '0003_rename_address_maintenancecompanyprofile_company_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='elevator',
            name='maintenance_company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='elevators', to='maintenance_companies.maintenancecompanyprofile'),
        ),
    ]
