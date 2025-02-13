from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
import uuid
from maintenance_companies.models import MaintenanceCompanyProfile
from account.models import User

class BrokerUserManager(BaseUserManager):
    """
    Custom manager for BrokerUser that creates a user with a referral_code.
    """
    def create_user(self, referral_code, email, password=None, **extra_fields):
        if not referral_code:
            raise ValueError("The referral code must be set")
        email = self.normalize_email(email)
        user = self.model(referral_code=referral_code, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class BrokerUser(AbstractUser):
    """
    Custom user model for brokers using UUID as primary key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Make referral_code the unique identifier (username)
    USERNAME_FIELD = 'referral_code'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'phone_number']

    # Broker-specific fields
    phone_number = models.CharField(max_length=15, unique=True, help_text="Phone number of the broker.")
    referral_code = models.CharField(max_length=8, unique=True, help_text="Unique referral code for the broker.")
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=12.5, help_text="Commission percentage earned by the broker (default is 12.5%).")
    commission_duration_months = models.PositiveIntegerField(default=24, help_text="Duration (in months) for which the broker earns commissions (default is 24 months).")
    registration_date = models.DateTimeField(default=timezone.now, help_text="Date when the broker registered.")

    # Set username to null so it doesn't conflict
    username = models.CharField(max_length=150, unique=False, blank=True, null=True)

    # Add unique related_name attributes to avoid clashes with other user models
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='broker_users',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='broker_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    objects = BrokerUserManager()  # Set custom manager for BrokerUser

    def __str__(self):
        return f"Broker: {self.email} | Referral Code: {self.referral_code}"
    
class BrokerReferral(models.Model):
    """
    Tracks maintenance companies registered by a broker using their referral code/link.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    broker = models.ForeignKey(BrokerUser, on_delete=models.CASCADE, related_name="referrals")
    maintenance_company = models.ForeignKey(MaintenanceCompanyProfile, on_delete=models.CASCADE, related_name="referral")
    referral_date = models.DateTimeField(default=timezone.now, help_text="Date when the maintenance company was referred.")
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=12.5, help_text="Commission percentage for this referral.")
    commission_duration_months = models.PositiveIntegerField(default=24, help_text="Duration (in months) for which the broker earns commissions for this referral.")

    def __str__(self):
        return f"Referral by {self.broker.email} for {self.maintenance_company.company_name}"

    class Meta:
        verbose_name = "Broker Referral"
        verbose_name_plural = "Broker Referrals"
        ordering = ['-referral_date']

