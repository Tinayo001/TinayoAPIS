from django.contrib import admin
from .models import TechnicianProfile

@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'maintenance_company', 'is_approved', 'created_at', 'updated_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'specialization']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'specialization', 'maintenance_company', 'is_approved')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


