from django.contrib import admin
from .models import (
    PaymentPlan,
    ExpectedPayment,
    Payment,
    RevenueSplit,
    BrokerBalance,
    WithdrawalRequest,
    PaymentSettings
)


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "maintenance_company", "amount_per_asset", "start_date", "end_date")
    search_fields = ("maintenance_company__company_name",)
    list_filter = ("start_date", "end_date")
    ordering = ("-start_date",)

@admin.register(ExpectedPayment)
class ExpectedPaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "maintenance_company", "total_amount", "status", "calculation_date", "due_date")
    search_fields = ("maintenance_company__company_name",)
    list_filter = ("status", "calculation_date", "due_date")
    ordering = ("-calculation_date",)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "maintenance_company", "amount", "payment_date", "transaction_id", "payment_method", "is_successful")
    search_fields = ("maintenance_company__company_name", "transaction_id")
    list_filter = ("payment_method", "is_successful", "payment_date")
    ordering = ("-payment_date",)

@admin.register(RevenueSplit)
class RevenueSplitAdmin(admin.ModelAdmin):
    list_display = ("id", "payment", "total_revenue", "broker_commission", "company_earnings", "split_date")
    search_fields = ("payment__transaction_id",)
    ordering = ("-split_date",)

@admin.register(BrokerBalance)
class BrokerBalanceAdmin(admin.ModelAdmin):
    list_display = ("id", "broker", "total_earnings", "expected_monthly_earnings", "withdrawable_amount", "last_updated")
    search_fields = ("broker__email",)
    ordering = ("-last_updated",)

@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "broker", "amount", "request_date", "status")
    search_fields = ("broker__email",)
    list_filter = ("status", "request_date")
    ordering = ("-request_date",)

@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "min_charge_per_elevator", "default_commission", "default_commission_duration", "default_calculation_date", "default_due_date")

