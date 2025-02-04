from django.contrib import admin
from .models import DeveloperProfile

@admin.register(DeveloperProfile)
class DeveloperProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'developer_name', 'address', 'specialization']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'developer_name', 'address', 'specialization']

