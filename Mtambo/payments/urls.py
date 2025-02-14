from django.urls import path
from .views import *

urlpatterns = [
    path('admin/configure_payment_settings/', ConfigurePaymentSettingsView.as_view(), name='configure-payment-settings'),
    path('admin/<int:broker_id>/configure_payment_settings/', BrokerCommissionSettingsView.as_view(), name='broker-commission-settings'),
]
