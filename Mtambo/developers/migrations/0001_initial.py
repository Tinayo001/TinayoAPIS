# Generated by Django 5.1.4 on 2025-01-13 09:23

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0002_remove_technician_maintenance_company_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeveloperProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('developer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='developer_profile', to='account.developer')),
            ],
        ),
    ]
