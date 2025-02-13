# Generated by Django 5.1.4 on 2025-02-13 11:51

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('maintenance_companies', '0004_alter_maintenancecompanyprofile_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrokerUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('phone_number', models.CharField(help_text='Phone number of the broker.', max_length=15, unique=True)),
                ('referral_code', models.CharField(help_text='Unique referral code for the broker.', max_length=8, unique=True)),
                ('commission_percentage', models.DecimalField(decimal_places=2, default=12.5, help_text='Commission percentage earned by the broker (default is 12.5%).', max_digits=5)),
                ('commission_duration_months', models.PositiveIntegerField(default=24, help_text='Duration (in months) for which the broker earns commissions (default is 24 months).')),
                ('registration_date', models.DateTimeField(default=django.utils.timezone.now, help_text='Date when the broker registered.')),
                ('username', models.CharField(blank=True, max_length=150, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='broker_users', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='broker_users', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BrokerReferral',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('referral_date', models.DateTimeField(default=django.utils.timezone.now, help_text='Date when the maintenance company was referred.')),
                ('commission_percentage', models.DecimalField(decimal_places=2, default=12.5, help_text='Commission percentage for this referral.', max_digits=5)),
                ('commission_duration_months', models.PositiveIntegerField(default=24, help_text='Duration (in months) for which the broker earns commissions for this referral.')),
                ('maintenance_company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referral', to='maintenance_companies.maintenancecompanyprofile')),
                ('broker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referrals', to='brokers.brokeruser')),
            ],
            options={
                'verbose_name': 'Broker Referral',
                'verbose_name_plural': 'Broker Referrals',
                'ordering': ['-referral_date'],
            },
        ),
    ]
