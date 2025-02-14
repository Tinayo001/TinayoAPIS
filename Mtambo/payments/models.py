import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from maintenance_companies.models import MaintenanceCompanyProfile
from brokers.models import BrokerUser
from elevators.models import Elevator  # Assuming Elevator model exists

class PaymentPlan(models.Model):
    """
    Defines the payment plan for maintenance companies.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    maintenance_company = models.ForeignKey(
        MaintenanceCompanyProfile, on_delete=models.CASCADE, related_name="payment_plans"
    )
    amount_per_asset = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=700.00,
        validators=[MinValueValidator(0)],
        help_text="Amount charged per elevator per month."
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment Plan for {self.maintenance_company.company_name} - Kshs. {self.amount_per_asset} per elevator/month"


class ExpectedPayment(models.Model):
    """
    Tracks expected payments by maintenance companies.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    maintenance_company = models.ForeignKey(
        MaintenanceCompanyProfile, on_delete=models.CASCADE, related_name="expected_payments"
    )
    assets = models.ManyToManyField(Elevator, related_name="expected_payments")
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    calculation_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.calculation_date = timezone.now().replace(day=25, hour=0, minute=0, second=0, microsecond=0)
            next_month = self.calculation_date.replace(day=28) + timezone.timedelta(days=4)
            self.due_date = next_month.replace(day=5, hour=23, minute=59, second=59)
            payment_plan = self.maintenance_company.payment_plans.first()
            self.total_amount = (payment_plan.amount_per_asset if payment_plan else 700.00) * self.assets.count()
        super().save(*args, **kwargs)

    def update_status(self):
        self.status = 'paid' if self.payment_date else ('overdue' if timezone.now() > self.due_date else 'pending')
        self.save()

    def __str__(self):
        return f"Expected Payment for {self.maintenance_company.company_name} - Kshs. {self.total_amount} ({self.get_status_display()})"


class Payment(models.Model):
    """
    Tracks payments made by maintenance companies.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    maintenance_company = models.ForeignKey(
        MaintenanceCompanyProfile, on_delete=models.CASCADE, related_name="payments"
    )
    expected_payment = models.ForeignKey(
        ExpectedPayment, on_delete=models.CASCADE, related_name="payments", null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_date = models.DateTimeField(default=timezone.now)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(
        max_length=50, choices=[('mpesa', 'M-PESA'), ('bank', 'Bank Transfer'), ('other', 'Other')], default='mpesa'
    )
    is_successful = models.BooleanField(default=True)

    def __str__(self):
        return f"Payment of Kshs. {self.amount} by {self.maintenance_company.company_name}"


class RevenueSplit(models.Model):
    """
    Tracks revenue split between broker, company, and platform.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="revenue_splits")
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    broker_commission = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    company_earnings = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    split_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Revenue Split for Payment ID: {self.payment.id}"


class BrokerBalance(models.Model):
    """
    Tracks broker financial balances.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    broker = models.ForeignKey(BrokerUser, on_delete=models.CASCADE, related_name="balances")
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    expected_monthly_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    withdrawable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(default=timezone.now)


class WithdrawalRequest(models.Model):
    """
    Tracks broker withdrawal requests.
    """
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    broker = models.ForeignKey(BrokerUser, on_delete=models.CASCADE, related_name="withdrawal_requests")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    request_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')


class PaymentSettings(models.Model):
    """
    Stores system-wide payment settings.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    min_charge_per_elevator = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    default_commission = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    default_commission_duration = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    default_calculation_date = models.PositiveIntegerField(default=20, validators=[MinValueValidator(1), MaxValueValidator(31)])
    default_due_date = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)])

