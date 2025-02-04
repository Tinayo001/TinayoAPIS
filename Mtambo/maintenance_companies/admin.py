from django.contrib import admin
from .models import MaintenanceCompanyProfile

@admin.register(MaintenanceCompanyProfile)
class MaintenanceCompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'company_address', 'specialization')  # Display valid fields
    search_fields = ('company_name', 'specialization')  # Search by company name or specialization
    list_filter = ('specialization',)  # Filter by specialization

