# Generated by Django 5.1.4 on 2025-01-13 09:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
        ('elevators', '0002_alter_elevator_maintenance_company_and_more'),
        ('maintenance_companies', '0002_remove_maintenancecompanyprofile_maintenance_and_more'),
        ('technicians', '0002_remove_technicianprofile_technician_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='technician',
            name='maintenance_company',
        ),
        migrations.RemoveField(
            model_name='technician',
            name='user',
        ),
        migrations.DeleteModel(
            name='Maintenance',
        ),
        migrations.DeleteModel(
            name='Technician',
        ),
    ]
