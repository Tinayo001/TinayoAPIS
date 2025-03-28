# Generated by Django 5.1.4 on 2025-01-13 09:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elevators', '0001_initial'),
        ('maintenance_companies', '0002_remove_maintenancecompanyprofile_maintenance_and_more'),
        ('technicians', '0002_remove_technicianprofile_technician_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='elevator',
            name='maintenance_company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='maintained_elevators', to='maintenance_companies.maintenancecompanyprofile'),
        ),
        migrations.AlterField(
            model_name='elevator',
            name='technician',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_elevators', to='technicians.technicianprofile'),
        ),
    ]
