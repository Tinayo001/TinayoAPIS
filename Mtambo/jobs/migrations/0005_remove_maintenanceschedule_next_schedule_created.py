# Generated by Django 5.1.4 on 2025-02-10 14:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_maintenanceschedule_next_schedule_created'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='maintenanceschedule',
            name='next_schedule_created',
        ),
    ]
