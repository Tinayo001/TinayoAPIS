# Generated by Django 5.1.4 on 2025-02-10 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_alter_maintenanceschedule_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='maintenanceschedule',
            name='next_schedule_created',
            field=models.BooleanField(default=False),
        ),
    ]
