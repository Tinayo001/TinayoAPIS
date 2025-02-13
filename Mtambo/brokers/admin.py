from django.contrib import admin
from .models import BrokerUser, BrokerReferral

class BrokerUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'referral_code', 'phone_number', 'commission_percentage', 'commission_duration_months', 'registration_date')
    search_fields = ('email', 'referral_code', 'phone_number')
    list_filter = ('commission_percentage', 'commission_duration_months', 'registration_date')
    ordering = ('-registration_date',)
    list_per_page = 20

class BrokerReferralAdmin(admin.ModelAdmin):
    list_display = ('broker', 'maintenance_company', 'referral_date', 'commission_percentage', 'commission_duration_months')
    search_fields = ('broker__email', 'maintenance_company__company_name')
    list_filter = ('commission_percentage', 'commission_duration_months', 'referral_date')
    ordering = ('-referral_date',)
    list_per_page = 20

# Register models to the admin site
admin.site.register(BrokerUser, BrokerUserAdmin)
admin.site.register(BrokerReferral, BrokerReferralAdmin)

