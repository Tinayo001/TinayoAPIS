# payments/serializers.py
from rest_framework import serializers
from brokers.models import BrokerUser


class PaymentSettingsSerializer(serializers.Serializer):
    """
    Serializer for configuring payment settings.
    Allows partial updates (one or more fields).
    """
    min_charge_per_elevator = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Default minimum charge per elevator per month."
    )
    default_commission = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        help_text="Default commission percentage for brokers (e.g., 12.5%)."
    )
    default_commission_duration = serializers.IntegerField(
        required=False,
        help_text="Default duration (in months) for which brokers earn commissions (e.g., 24 months)."
    )
    default_calculation_date = serializers.IntegerField(
        required=False,
        help_text="Default day of the month for calculating expected payments (e.g., 25th)."
    )
    default_due_date = serializers.IntegerField(
        required=False,
        help_text="Default day of the month for payment due dates (e.g., 5th)."
    )


class BrokerCommissionSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and updating broker commission settings.
    """
    class Meta:
        model = BrokerUser
        fields = [
            'first_name', 'last_name', 'referral_code',
            'commission_percentage', 'commission_duration_months', 'registration_date'
        ]
        read_only_fields = ['first_name', 'last_name', 'referral_code', 'registration_date']  # These fields cannot be updated
