from django.contrib import admin
from .models import Alert

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'message', 'recipient_type', 'recipient_id', 'content_type', 'object_id', 'created_at', 'is_read')
    list_filter = ('alert_type', 'is_read', 'created_at')
    search_fields = ('message', 'recipient_id', 'object_id')
    ordering = ('-created_at',)


